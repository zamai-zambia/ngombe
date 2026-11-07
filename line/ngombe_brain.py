"""The Ng'ombe line's reader and writer (7 Nov 2026; Chris: "The triage needs to be smarter than that, more natural").

One model call per message from a Ng'ombe user. The model gets the person's profile, herd, recent entries, the last
messages of the thread, the translator's reading when the words are not English, and the photo if one came. It writes
the reply in its own words and files what the message says through tools; the watcher executes the tools against the
cattle backend. No fixed sentences anywhere. Claude Sonnet 5.5 (NGOMBE_MODEL to change), low effort, strict tools, the system prompt cached.

    from ngombe_brain import think
    reply, actions = think(ctx, execute)      # execute(name, input) -> str, called for every tool the model uses
"""
import base64
import json
import os

import anthropic

NL = chr(10)
TRAIN_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "internal", "zamai_line", "ngombe_brain_log.jsonl")
MODEL = os.environ.get("NGOMBE_MODEL") or "claude-sonnet-5-5"   # Chris, 7 Nov 2026: "If sonnet can handle it, definitely cheaper"
ZP_ENV = r"C:\Users\Chris\projects\ZamaiPort\.env.local"


def _key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    for line in open(ZP_ENV, encoding="utf-8"):
        if line.startswith("ANTHROPIC_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("ANTHROPIC_API_KEY missing")


SYSTEM = """You are the Ng'ombe records line: Christoph Lindinger's AI assistant on the Zamai WhatsApp line, keeping the
record of a smallholder's cattle in Southern Province, Zambia. You read what the person writes, in English, Tonga or a
mix, and you keep their records straight. Say you are an AI assistant to anyone who asks or seems unsure.

What you do with a message
- A report on an animal (sick, limping, not eating, dipped, vaccinated, treated, weighed, calved, sold, died, moved):
  file it with file_event on the right animal, then confirm in one or two plain sentences what you filed and when.
  Use the person's own words for the text of the entry. If the animal is not named and the herd has several, ask
  which one, in one short question; if the herd has exactly one, assume it. If the name is not in the herd, ask
  whether it is a new animal, or register it when the person clearly says so.
- "Dipped all" or the like: file the event on every live animal.
- A photo: it has been stored; attach it to the animal with attach_photo when you know which one. Do not describe
  the animal's condition from the photo and do not read anything medical into it: a separate, trained visual model
  will do that later. You may say what the picture is (a cow, a calf, a document, not an animal) and nothing more.
- A death or a sale: file the event and set_status.
- A new animal: register_animal; class 'unknown' is fine when the person does not say.
- Feedback about the app or the line, a complaint, a question about how things work: answer it as yourself, plainly,
  and call tell_chris with the gist so Christoph sees it.
- Money, meetings, dates, the President, anything you cannot place: tell_chris and say you will check with Christoph.
- A greeting or thanks: answer like a person would, one line.

How you write
- WhatsApp register: short, warm, direct. One point, at most one question. No lists unless the person asks.
- English unless the person clearly writes Tonga; then a Tonga greeting is fine, but do not compose Tonga sentences
  beyond a greeting: our Tonga comes from speakers, not from you. Quote their Tonga back when confirming an entry.
- Never diagnose or treat. A sick animal belongs to the veterinary assistant or officer; say the report is in the
  record for them and, when it sounds urgent, say to call the vet now.
- Never invent records, names or numbers. What you know is in the context you are given.
- No em or en dashes. No links except https://ngombe.zamai.pro/my/ when the person asks where to see their records.
- Do not add a signature; the line adds " *cd" itself.
- Write the reply as plain text. Call the tools first, then write the reply that reports what you did."""

TOOLS = [
    {"name": "file_event", "description": "File an entry on one animal (or on the herd when animal is empty and the event concerns no single animal).",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["animal", "kind", "text"],
                      "properties": {"animal": {"type": "string", "description": "the animal's name exactly as in the herd list, or '' for a herd-level entry"},
                                     "kind": {"type": "string", "enum": ["sick_report", "dipped", "vaccinated", "treated", "weighed", "born", "weaned", "moved", "sold", "died", "note"]},
                                     "text": {"type": "string", "description": "the person's own words for this entry"},
                                     "kg": {"type": ["number", "null"], "description": "weight in kg for 'weighed', else null"}}},
     "strict": True},
    {"name": "file_event_all", "description": "File the same entry on every live animal in the herd (dip day, vaccination round).",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["kind", "text"],
                      "properties": {"kind": {"type": "string", "enum": ["dipped", "vaccinated", "treated", "moved", "note"]},
                                     "text": {"type": "string"}}},
     "strict": True},
    {"name": "register_animal", "description": "Register a new animal in this person's herd.",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["name", "class", "sex"],
                      "properties": {"name": {"type": "string"},
                                     "class": {"type": "string", "enum": ["calf", "weaner", "heifer", "cow", "bull", "steer", "ox", "unknown"]},
                                     "sex": {"type": "string", "enum": ["f", "m", "unknown"]},
                                     "tag": {"type": ["string", "null"]}}},
     "strict": True},
    {"name": "set_status", "description": "Mark an animal sold, dead or lost (after filing the event).",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["animal", "status"],
                      "properties": {"animal": {"type": "string"}, "status": {"type": "string", "enum": ["sold", "dead", "lost", "alive"]}}},
     "strict": True},
    {"name": "attach_photo", "description": "Attach the photo that came with this message to an animal.",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["animal"],
                      "properties": {"animal": {"type": "string"}}},
     "strict": True},
    {"name": "tell_chris", "description": "Send Christoph a one-line note on his phone: feedback, a complaint, a question you cannot answer, money, meetings, anything for him.",
     "input_schema": {"type": "object", "additionalProperties": False, "required": ["note"],
                      "properties": {"note": {"type": "string", "description": "one line, no personal details beyond the first name"}}},
     "strict": True},
]


def think(ctx, execute, log=print):
    """ctx: {profile, animals, events, thread, message, reading, photo_bytes, just_tied}. Returns (reply, actions)."""
    # inside a Claude Code session the environment carries its own OAuth token, which the SDK would prefer over the key
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE", "ANTHROPIC_BASE_URL")}
    os.environ.clear()
    os.environ.update(env)
    client = anthropic.Anthropic(api_key=_key(), auth_token=None, timeout=60.0, max_retries=1)
    lines = []
    p = ctx.get("profile") or {}
    lines.append(f"Person: {p.get('name', '?')}, {p.get('place') or 'place unknown'}, {p.get('district') or 'district unknown'}, "
                 f"number {ctx.get('number')}, profile made {'from the WhatsApp line' if p.get('created_via') == 'line' else 'in the app'}.")
    if ctx.get("just_tied"):
        lines.append("This number was tied to the profile a moment ago with the code the person just sent: greet them, "
                     "say the number is now tied, in one or two lines.")
    an = ctx.get("animals") or []
    if an:
        lines.append("Herd: " + "; ".join(f"{a['name']} ({a.get('class')}, {a.get('sex') or '?'}, tag {a.get('tag') or 'none'}, {a.get('status')}"
                                          + (f", notes: {a['notes']}" if a.get('notes') else "") + ")" for a in an))
    else:
        lines.append("Herd: no animals registered yet.")
    ev = ctx.get("events") or []
    if ev:
        lines.append("Last entries (newest first): " + "; ".join(ev))
    th = ctx.get("thread") or []
    if th:
        lines.append("Last messages on this thread (oldest first):\n" + "\n".join(th))
    msg = ctx.get("message") or ""
    lines.append(f"NEW MESSAGE from the person, {ctx.get('when')}: {msg!r}" if msg else f"NEW MESSAGE from the person, {ctx.get('when')}: a photo with no words")
    if ctx.get("reading"):
        lines.append(f"Our translator reads the Tonga as: {ctx['reading']!r} (machine reading; treat it as probable, not certain).")
    if ctx.get("photo_bytes"):
        lines.append("A photo came with the message; it is attached below and already stored. Attach it to the animal when you know which one.")
    content = [{"type": "text", "text": "\n".join(lines)}]
    if ctx.get("photo_bytes"):
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                    "data": base64.b64encode(ctx["photo_bytes"]).decode()}})
    messages = [{"role": "user", "content": content}]
    actions = []
    reply = ""
    for _ in range(5):
        r = client.messages.create(
            model=MODEL, max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            output_config={"effort": "low"},
            tools=TOOLS, messages=messages)
        if r.stop_reason == "refusal":
            log(f"brain: refusal ({getattr(r.stop_details, 'category', None)})")
            return "", actions
        texts = [b.text for b in r.content if b.type == "text"]
        uses = [b for b in r.content if b.type == "tool_use"]
        if texts:
            reply = "\n".join(t.strip() for t in texts if t.strip())
        if r.stop_reason != "tool_use" or not uses:
            break
        messages.append({"role": "assistant", "content": r.content})
        results = []
        for u in uses:
            inp = u.input if isinstance(u.input, dict) else json.loads(u.input)
            try:
                out = execute(u.name, inp)
                actions.append((u.name, inp, out))
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": str(out)})
            except Exception as e:  # noqa: BLE001
                actions.append((u.name, inp, f"ERROR {e}"))
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": f"failed: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})
    try:
        u = r.usage
        log(f"brain: in {u.input_tokens} (cached {getattr(u, 'cache_read_input_tokens', 0) or 0}) out {u.output_tokens}, {len(actions)} action(s)")
    except Exception:  # noqa: BLE001
        pass
    # every exchange is a training example for the local expert model later (Chris, 7 Nov 2026: "it is part of our
    # idea, local expert model"): the context the model saw, what it called, what it wrote. No photo bytes.
    try:
        with open(TRAIN_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": ctx.get("when"), "number": ctx.get("number"), "model": MODEL, "context": NL.join(lines),
                                "had_photo": bool(ctx.get("photo_bytes")), "actions": [(a, i, str(o)[:200]) for a, i, o in actions],
                                "reply": reply.strip(), "dry": ctx.get("dry", False)}, ensure_ascii=False) + NL)
    except Exception as e:  # noqa: BLE001
        log(f"brain: could not write the training log: {e}")
    return reply.strip(), actions

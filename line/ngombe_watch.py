"""Ng'ombe line watcher (7 Nov 2026; Chris: "if we want it to work as a demo, it needs to be responsive").

An always-on loop beside the standby responder. Every few seconds it reads new inbound messages on the Zamai line and
handles, WITHOUT A MODEL and within seconds, everything the cattle records app ngombe.zamai.pro/my/ needs:

  "Ngombe 123456" / "123456"      the binding code: ties the sender's number to the profile that made the code
  a photo, with or without words   stored in the person's cattle-photos folder, filed as an event
  "Chipego: limping since Monday"  a report on a named animal (the app's "Report sick" link writes "Name: ")
  "dipped all today"               dip day for the whole herd
  "my cow is sick" in English or Tonga, or mixed: Tonga is read through our translator, the reading is kept with the
                                   original in the event, and the reply quotes both
  a bare animal name               answers the watcher's own "Which animal is it?"

Anything else from a Ng'ombe user (a question, a conversation) is left to the standby session, which answers with a
model within a few minutes. People who are not tied to a profile are not touched at all.

Writes go to the self-hosted backend (NGOMBE_SUPABASE_URL, default http://127.0.0.1:8000, service key from
ZamaiPort/.env.local); events carry source 'whatsapp' and the WhatsApp message id. Replies go through zamai_send.py
(its guards: 24 h window, no dashes, logged to zamai_messages). Fixed reply texts: ngombe_replies.json (English now,
Tonga from a speaker later, then both lines in one message). Sick reports send Chris an ntfy status line.

    python -X utf8 tools/zamai_line/ngombe_watch.py                loop (the scheduled task "Ngombe line watcher")
    python -X utf8 tools/zamai_line/ngombe_watch.py --once         one pass, then exit
    python -X utf8 tools/zamai_line/ngombe_watch.py --dry "text"   classify a text for Chris's number, send nothing
    python -X utf8 tools/zamai_line/ngombe_watch.py --herd 2609... the profile, animals and last events (for the
                                                                   standby session, which must not open the DB itself)
    python -X utf8 tools/zamai_line/ngombe_watch.py --media in/x.jpg out.jpg   fetch a line photo from storage
State: internal/zamai_line/ngombe_watch.json (cursor, pending questions), ngombe_watch.log, ngombe_watch.heartbeat.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(REPO, "internal", "zamai_line")
ZP = r"C:\Users\Chris\projects\ZamaiPort"
sys.path.insert(0, os.path.join(ZP, "automation", "scripts"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
from responder_common import sb, URL as YURL, KEY as YKEY, parse_ts, ZAMBIA  # noqa: E402
import zamai_round as Z  # noqa: E402
from ngombe_brain import think  # noqa: E402

LINE = "260776621255"
POLL_S = 3
SPACE = "https://gijoehansfranz-zamai-tonga.hf.space"
STATE_FILE = os.path.join(STATE, "ngombe_watch.json")
LOG = os.path.join(STATE, "ngombe_watch.log")
HEART = os.path.join(STATE, "ngombe_watch.heartbeat")


def env_value(path, name):
    if not os.path.exists(path):
        return ""
    for line in open(path, encoding="utf-8"):
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip()
    return ""


NURL = os.environ.get("NGOMBE_SUPABASE_URL") or "http://127.0.0.1:8000"
NKEY = os.environ.get("NGOMBE_SUPABASE_SERVICE_ROLE_KEY") or env_value(os.path.join(ZP, ".env.local"), "NGOMBE_SUPABASE_SERVICE_ROLE_KEY")
TONGA_KEY = env_value(os.path.join(REPO, ".env.local"), "TONGA_KEY")


def log(msg):
    os.makedirs(STATE, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  {msg}\n")


def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE, encoding="utf-8"))
    return {"cursor": dt.datetime.now(dt.timezone.utc).isoformat(), "pending": {}, "seen": []}


def save_state(s):
    os.makedirs(STATE, exist_ok=True)
    json.dump(s, open(STATE_FILE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


# ── the cattle backend ──────────────────────────────────────────────────────────────────────────────────────────
def n(path, method="GET", body=None, prefer=None):
    h = {"apikey": NKEY, "Authorization": "Bearer " + NKEY, "Content-Type": "application/json",
         "Accept-Profile": "cattle", "Content-Profile": "cattle"}
    if prefer:
        h["Prefer"] = prefer
    req = urllib.request.Request(NURL + "/rest/v1/" + path, method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            t = r.read().decode()
        return json.loads(t) if t else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"backend HTTP {e.code} on {method} {path.split('?')[0]}: {e.read().decode(errors='replace')[:300]}") from None


def profile_by_phone(num):
    rows = n(f"profiles?phone=eq.{num}&select=id,name,place,district,phone")
    return rows[0] if rows else None


def animals_of(uid):
    return n(f"animals?owner=eq.{uid}&select=id,name,class,sex,tag,status&order=created_at") or []


def write_event(uid, animal, kind, data, at):
    rows = n("events", "POST", {"owner": uid, "animal": animal, "kind": kind, "data": data, "source": "whatsapp", "at": at},
             prefer="return=representation")
    return rows[0]["id"] if rows else None


def set_status(animal_id, status):
    n(f"animals?id=eq.{animal_id}", "PATCH", {"status": status}, prefer="return=minimal")


def line_media(media_path):
    req = urllib.request.Request(f"{YURL}/storage/v1/object/whatsapp-media/{media_path}",
                                 headers={"apikey": YKEY, "Authorization": "Bearer " + YKEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def store_photo(uid, data, stamp):
    path = f"{uid}/line/{stamp}.jpg"
    req = urllib.request.Request(f"{NURL}/storage/v1/object/cattle-photos/{path}", method="POST", data=data,
                                 headers={"apikey": NKEY, "Authorization": "Bearer " + NKEY,
                                          "Content-Type": "image/jpeg", "x-upsert": "true"})
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()
    return path, hashlib.sha256(data).hexdigest()


# ── reading the words ───────────────────────────────────────────────────────────────────────────────────────────
CODE = re.compile(r"^\s*(?:ng'?ombe\s*)?(\d{6})\s*$", re.I)


def translate(text):
    """Tonga (or mixed) to English through our translator Space. Returns the English or '' when it cannot."""
    if not TONGA_KEY:
        return ""
    req = urllib.request.Request(SPACE + "/translate", method="POST",
                                 data=json.dumps({"text": text[:2000], "src": "toi"}).encode(),
                                 headers={"Content-Type": "application/json", "X-Tonga-Key": TONGA_KEY})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            res = json.loads(r.read().decode())
        return " ".join((s.get("out") or "").strip() for s in res.get("sentences", [])).strip()
    except Exception as e:  # noqa: BLE001
        log(f"translator failed: {e}")
        return ""


def looks_english(text):
    """Cheap test: most words are in a small English function-word set, or there are no letters at all."""
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return True
    common = {"the", "a", "an", "is", "are", "was", "my", "our", "it", "its", "has", "have", "and", "to", "of", "in",
              "on", "at", "for", "not", "no", "all", "today", "yesterday", "since", "this", "that", "with", "from",
              "cow", "bull", "calf", "heifer", "ox", "cattle", "animal", "animals", "sick", "dip", "dipped", "died",
              "sold", "limping", "eating", "walking", "please", "help", "i", "we", "he", "she", "they", "morning"}
    return sum(w in common for w in words) >= max(1, len(words) // 3)


def send(to, body, dry=False):
    body = body.rstrip() + " *cd"
    if dry:
        print(f"WOULD SEND to {to}:\n{body}\n")
        return True
    cmd = [sys.executable.replace("pythonw.exe", "python.exe"), os.path.join(ZP, "automation", "scripts", "zamai_send.py"),
           "--to", to, "--text", body, "--allow-followup"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, cwd=ZP, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                       timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    ok = r.returncode == 0
    log(f"send to {to}: {'ok' if ok else 'FAILED ' + (r.stdout + r.stderr).strip()[-300:]}")
    return ok


def wake_standby(num):
    """Start the standby check now instead of waiting for its 2-minute tick (Chris, 7 Nov 2026: "The response time is
    too slow"). One at a time: a lock file younger than 15 minutes means a session is still running."""
    lock = os.path.join(STATE, "standby.lock")
    try:
        if os.path.exists(lock) and (time.time() - os.path.getmtime(lock)) < 15 * 60:
            return
        open(lock, "w").write("wake")
        pyw = sys.executable if sys.executable.endswith("pythonw.exe") else sys.executable.replace("python.exe", "pythonw.exe")
        subprocess.Popen([pyw, os.path.join(HERE, "standby.pyw"), "--force", num], cwd=REPO,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as e:  # noqa: BLE001
        log(f"could not wake the standby: {e}")


def note(text):
    try:
        import notify
        notify.send(text, title="Ng'ombe")
    except Exception as e:  # noqa: BLE001
        log(f"ntfy failed: {e}")


def hm(iso):
    d = parse_ts(iso)
    return d.astimezone(ZAMBIA).strftime("%H:%M") if d else "?"


# ── one inbound message ─────────────────────────────────────────────────────────────────────────────────────────
def tie(num, code, m):
    """A code from the app: tie the number to the profile that made it. Returns (profile or None, status)."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=15)).isoformat()
    rows = n(f"phone_codes?code=eq.{code}&used_at=is.null&created_at=gte.{urllib.parse.quote(since)}&select=code,profile")
    if not rows:
        return profile_by_phone(num), "no_such_code"
    uid = rows[0]["profile"]
    other = n(f"profiles?phone=eq.{num}&id=neq.{uid}&select=id,created_via")
    if other and other[0].get("created_via") != "line":
        return profile_by_phone(num), "taken"
    if other:
        n("rpc/merge_line_profile", "POST", {"line_profile": other[0]["id"], "app_profile": uid})
        log(f"merged line profile {other[0]['id']} into {uid}")
    n(f"profiles?id=eq.{uid}", "PATCH", {"phone": num, "phone_bound_at": dt.datetime.now(dt.timezone.utc).isoformat()}, prefer="return=minimal")
    n(f"phone_codes?code=eq.{code}", "PATCH", {"used_at": dt.datetime.now(dt.timezone.utc).isoformat()}, prefer="return=minimal")
    write_event(uid, None, "note", {"note": "phone tied through the Zamai line", "via": "line"}, m["created_at"])
    log(f"tied {num} to profile {uid}")
    return profile_by_phone(num), "tied"


def create_line_profile(num, wa_name):
    """A code sent by a number the backend does not know, and the code matches nothing: the number gets its own
    records (Chris, 7 Nov 2026: "Anyone who sends an ngombe code gets a profile automatically")."""
    name = (wa_name or "").strip()[:80]
    if len(name) < 2:
        name = "Herder " + num[-4:]
    h = {"apikey": NKEY, "Authorization": "Bearer " + NKEY, "Content-Type": "application/json"}
    req = urllib.request.Request(NURL + "/auth/v1/admin/users", method="POST", headers=h,
                                 data=json.dumps({"email": f"{num}@line.ngombe.invalid", "email_confirm": True,
                                                  "user_metadata": {"via": "line"}}).encode())
    with urllib.request.urlopen(req, timeout=20) as r:
        uid = json.loads(r.read().decode())["id"]
    n("profiles", "POST", {"id": uid, "name": name, "phone": num, "phone_bound_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "created_via": "line"}, prefer="return=minimal")
    write_event(uid, None, "note", {"note": "profile made from the WhatsApp line", "via": "line"}, dt.datetime.now(dt.timezone.utc).isoformat())
    log(f"line profile made for {num} ({name}) -> {uid}")
    return profile_by_phone(num)


def thread_lines(num, limit=12):
    rows = sb(f"zamai_messages?counterparty=eq.{num}&select=created_at,direction,msg_type,body&order=created_at.desc&limit={limit}") or []
    out = []
    for r in reversed(rows):
        who = "them" if r["direction"] == "in" else "line"
        body = (r.get("body") or "").replace("\n", " ")
        if r.get("msg_type") == "image":
            body = "[photo] " + body.replace("[image]", "").strip()
        out.append(f"{hm(r['created_at'])} {who}: {body[:300]}")
    return out


def recent_events(uid, animals, limit=12):
    names = {a["id"]: a["name"] for a in animals}
    ev = n(f"events?owner=eq.{uid}&select=animal,kind,at,data,source&order=id.desc&limit={limit}") or []
    out = []
    for e in ev:
        d = e.get("data") or {}
        what = d.get("text") or d.get("note") or (f"{d.get('kg')} kg" if d.get("kg") else "")
        out.append(f"{hm(e['at'])} {e['kind']} {names.get(e.get('animal'), '(herd)')} via {e['source']}" + (f": {what[:80]}" if what else ""))
    return out


def handle(m, state, dry=False):
    num = str(m["counterparty"])
    if num == LINE:
        return
    body = (m.get("body") or "").strip()
    text = "" if body in ("[image]", "[sticker]", "[audio]", "[video]", "[document]", "[interactive]", "[location]", "[reaction]") else body
    is_image = (m.get("msg_type") == "image") and bool(m.get("media_path"))
    at = m["created_at"]

    just_tied = False
    prof = None
    c = CODE.match(text) if text else None
    if c and not dry:
        prof, status = tie(num, c.group(1), m)
        if status == "no_such_code" and not prof:
            prof = create_line_profile(num, m.get("wa_name"))
        just_tied = status in ("tied",) or (status == "no_such_code")
        if status == "taken":
            log(f"{num}: code for a number already tied to another app profile; the model explains")
    prof = prof or profile_by_phone(num)
    if not prof:
        log(f"{num}: no profile, left to the standby session ({text[:60]!r})")
        return

    uid = prof["id"]
    animals = animals_of(uid)
    photo = sha = photo_bytes = None
    if is_image:
        photo_bytes = open(os.path.join(REPO, "site", "cattle-demo", "photos", "a5.jpg"), "rb").read() if m["media_path"] == "dry" else line_media(m["media_path"])
        stamp = re.sub(r"\D", "", at)[:14]
        if not dry:
            photo, sha = store_photo(uid, photo_bytes, stamp)
    reading = ""
    if text and not looks_english(text):
        en = translate(text)
        if en and en.lower() != text.lower():
            reading = en

    def find(name):
        name = (name or "").strip().lower()
        for a in animals:
            if a["name"].lower() == name or (a.get("tag") and str(a["tag"]).lower() == name):
                return a
        raise ValueError(f"no animal called {name!r} in the herd; the names are " + ", ".join(a["name"] for a in animals))

    def execute(name, inp):
        if dry:
            return f"dry run: {name} {json.dumps(inp)}"
        if name == "file_event":
            data = {"text": inp["text"], "via": "line", "wa_message_id": m.get("wa_message_id")}
            if reading:
                data["text_en"], data["lang"] = reading, "to"
            if inp.get("kg") is not None:
                data["kg"] = inp["kg"]
            if photo:
                data["photo"], data["sha256"] = photo, sha
            a = find(inp["animal"]) if inp["animal"] else None
            eid = write_event(uid, a["id"] if a else None, inp["kind"], data, at)
            return f"filed event {eid} ({inp['kind']}) on {a['name'] if a else 'the herd'} at {hm(at)}"
        if name == "file_event_all":
            alive = [a for a in animals if a.get("status") == "alive"]
            for a in alive:
                write_event(uid, a["id"], inp["kind"], {"text": inp["text"], "via": "line", "wa_message_id": m.get("wa_message_id")}, at)
            return f"filed {inp['kind']} on {len(alive)} animals: " + ", ".join(a["name"] for a in alive)
        if name == "register_animal":
            row = {"owner": uid, "name": inp["name"][:60], "class": inp["class"], "sire_kind": "unknown"}
            if inp.get("sex") in ("f", "m"):
                row["sex"] = inp["sex"]
            if inp.get("tag"):
                row["tag"] = inp["tag"]
            a = n("animals", "POST", row, prefer="return=representation")[0]
            animals.append(a)
            write_event(uid, a["id"], "registered", {"via": "line", "class": inp["class"]}, at)
            return f"registered {a['name']} ({inp['class']})"
        if name == "set_status":
            a = find(inp["animal"])
            set_status(a["id"], inp["status"])
            return f"{a['name']} is now {inp['status']}"
        if name == "attach_photo":
            if not photo:
                return "no photo came with this message"
            a = find(inp["animal"])
            n("photos", "POST", {"owner": uid, "animal": a["id"], "kind": "other", "path": photo, "sha256": sha, "taken_at": at}, prefer="return=minimal")
            write_event(uid, a["id"], "photo", {"path": photo, "sha256": sha, "via": "line"}, at)
            return f"photo attached to {a['name']}"
        if name == "tell_chris":
            note(f"Ng'ombe, {prof.get('name', '?').split()[0]}: {inp['note'][:160]}")
            return "Christoph has the note"
        return f"unknown tool {name}"

    ctx = {"number": num, "profile": prof, "animals": animals, "events": recent_events(uid, animals),
           "thread": thread_lines(num), "message": text, "when": hm(at), "reading": reading,
           "photo_bytes": photo_bytes, "just_tied": just_tied, "dry": dry}
    try:
        reply, actions = think(ctx, execute, log=log)
    except Exception as e:  # noqa: BLE001
        # no key, no network, a refusal: the standby session answers instead, so nobody is left without an answer
        log(f"{num}: brain failed ({type(e).__name__}: {str(e)[:160]}); standby session woken")
        if not dry:
            wake_standby(num)
        return
    for name, inp, out in actions:
        log(f"{num}: {name} {json.dumps(inp, ensure_ascii=False)[:160]} -> {str(out)[:120]}")
    if not reply:
        log(f"{num}: the model wrote nothing; standby session woken")
        if not dry:
            wake_standby(num)
        return
    send(num, reply, dry)
    Z.mark(num)



# ── the loop ────────────────────────────────────────────────────────────────────────────────────────────────────
LOOKBACK_MIN = 90   # Meta stamps a message with its send time and can deliver it minutes later (Matthew's code, 7 Nov 2026:
                    # sent 12:28, delivered 12:35), so the window is by time and "seen" ids keep each message once


def fetch_new(cursor, floor=""):
    # never before the floor: the cursor at the watcher's first start, so old threads are not re-answered on a restart
    since = max(floor, min(cursor, (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=LOOKBACK_MIN)).isoformat()))
    return sb("zamai_messages?direction=eq.in&select=id,created_at,counterparty,wa_name,msg_type,body,media_path,wa_message_id"
              f"&created_at=gt.{urllib.parse.quote(since)}&order=created_at.asc&limit=100") or []


def tick(state):
    state.setdefault("floor", state["cursor"])
    rows = fetch_new(state["cursor"], state["floor"])
    for m in rows:
        if m["id"] in state["seen"]:
            continue
        lag = (dt.datetime.now(dt.timezone.utc) - parse_ts(m["created_at"])).total_seconds()
        if lag > 60:
            log(f"late delivery: message from {m['counterparty']} stamped {m['created_at'][11:19]} arrived {lag / 60:.1f} min later")
        try:
            handle(m, state)
        except Exception:  # noqa: BLE001
            log(f"ERROR on message {m['id']} from {m['counterparty']}: " + traceback.format_exc().replace("\n", " | "))
        state["seen"] = (state["seen"] + [m["id"]])[-1000:]
        state["cursor"] = max(state["cursor"], m["created_at"])
        save_state(state)
    open(HEART, "w").write(dt.datetime.now(dt.timezone.utc).isoformat())


def herd_report(num):
    prof = profile_by_phone(num)
    if not prof:
        print(f"{num}: no Ng'ombe profile tied to this number")
        return
    print(f"{prof['name']} ({prof.get('place') or '?'}, {prof.get('district') or '?'}), profile {prof['id']}")
    for a in animals_of(prof["id"]):
        print(f"  {a['name']}: {a['class']}, {a.get('sex') or '?'}, tag {a.get('tag') or '-'}, {a['status']}  [{a['id'][:8]}]")
    ev = n(f"events?owner=eq.{prof['id']}&select=id,animal,kind,at,data,source&order=id.desc&limit=15") or []
    names = {a["id"]: a["name"] for a in animals_of(prof["id"])}
    for e in ev:
        d = e.get("data") or {}
        print(f"  {hm(e['at'])} {e['kind']} {names.get(e.get('animal'), '(herd)')} {e['source']}: {d.get('text') or d.get('note') or d.get('kg') or ''}"
              + (f" | read as: {d['text_en']}" if d.get("text_en") else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", metavar="TEXT")
    ap.add_argument("--image", action="store_true", help="with --dry: pretend the text came with a picture")
    ap.add_argument("--number", default="260962653100")
    ap.add_argument("--herd", metavar="NUMBER")
    ap.add_argument("--media", nargs=2, metavar=("MEDIA_PATH", "OUT"))
    a = ap.parse_args()
    if a.herd:
        herd_report(a.herd)
        return
    if a.media:
        open(a.media[1], "wb").write(line_media(a.media[0]))
        print(f"saved {a.media[1]}")
        return
    if a.dry is not None:
        state = {"cursor": "", "pending": {}, "seen": []}
        m = {"id": 0, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "counterparty": a.number,
             "msg_type": "image" if a.image else "text", "body": a.dry or "[image]", "media_path": "dry" if a.image else None, "wa_message_id": "dry"}
        handle(m, state, dry=True)
        return
    state = load_state()
    if a.once:
        tick(state)
        return
    log(f"watcher started, cursor {state['cursor']}")
    while True:
        try:
            tick(state)
        except Exception:  # noqa: BLE001
            log("ERROR " + traceback.format_exc().replace("\n", " | "))
            time.sleep(20)
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()

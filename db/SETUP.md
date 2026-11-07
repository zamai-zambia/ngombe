# Ng'ombe live app: the setup on the Beelink (started 7 Nov 2026, Chris's yes the same evening)

The database and the app's backend live on our machine, first the Beelink, next week the new machine (copy the folder
and the volumes). Self-hosted Supabase: Postgres, PostgREST, auth, storage, Studio, behind Kong. Reached from the
static app on Netlify through a Cloudflare quick tunnel this week (random address, published to a Netlify blob), a
fixed address on the new machine.

## Pieces, where they are

| Piece | Where | State |
|---|---|---|
| Supabase self-hosting files (`docker/` only, sparse clone) | `C:/Users/Chris/zamai-supabase/docker` | fetched 7 Nov |
| Our environment (secrets) | `C:/Users/Chris/zamai-supabase/docker/.env` | generated 7 Nov; NEVER in a repo |
| cloudflared | `C:/Users/Chris/tools/cloudflared.exe` (2026.10.7) | fetched 7 Nov |
| Docker Desktop installer | `C:/Users/Chris/Downloads/2026-11-07/installers/` | downloading 7 Nov; needs an elevated install |
| WSL 2 | `wsl --install --no-distribution`, elevated | launched 7 Nov; needs the UAC click and a reboot |
| Schema | `internal/cattle/app/schema.sql` | drafted; apply after the stack runs |
| Terms v0.1 | `internal/cattle/app/TERMS_v0.1.md` | drafted; Chris decides the text; Tonga from a speaker |
| The app screens (My herd) | `site/cattle-demo/my/` | to write |
| The WhatsApp binding function | `netlify/functions/ngombe-bind.mjs` | to write; reads the Zamai line's table for the code |

## Order of work

1. Reboot after WSL; install Docker Desktop (WSL 2 backend); confirm `docker compose version`.
2. `cd C:/Users/Chris/zamai-supabase/docker && docker compose up -d`; Studio on http://localhost:8000 with the dashboard
   password from `.env`; Postgres on 5432 with the password from `.env`.
3. Apply `schema.sql` (psql inside the db container); set the terms text; create the `cattle-photos` bucket (the schema
   does it).
4. Tunnel: `cloudflared tunnel --url http://localhost:8000`; the Beelink publishes the URL to the Netlify blob
   `ngombe-api` through `netlify/functions/ngombe-api-url.mjs` (write it) with `DESK_KEY`; the app reads it.
5. The app: profile (anonymous sign-in on the self-hosted auth, enabled in `.env`), terms acceptance, animals,
   photos to the bucket, the WhatsApp binding by code.
6. The responder brief: a cattle contact's herd is visible to the Zamai line responder (read-only query tool).

## Rules

- The Beelink is a Yumi machine: the ERP comes first; the stack is limited to 4 GB in Docker Desktop's settings.
- Secrets stay in `docker/.env` and in `C:/Users/Chris/projects/ZamaiPort/.env.local` (the anon and service keys for the
  functions); nothing in any repo.
- Row-level security on every table; the browser holds only the anon key and the user's token.

## The line watcher (7 Nov 2026)

`tools/zamai_line/ngombe_watch.py` is the always-on loop that makes the WhatsApp side responsive: codes, photos,
reports on named animals, dip day, deaths, sales, calves and sick reports in English, Tonga or mixed (Tonga read
through the translator Space with TONGA_KEY; original and reading both kept in the event). No model, replies within
seconds through zamai_send.py, fixed texts in `tools/zamai_line/ngombe_replies.json` (English now; the Tonga column is
filled from Matthew's chat lines, then both lines go in one message, so there is no language setting in the app:
Chris, 7 Nov: "we need to be able to handle both, plus mixed"). Questions are left to the standby session (model, a
few minutes), which reads the person's herd with `--herd <number>`. Register it once with
`powershell -ExecutionPolicy Bypass -File tools\zamai_line\install_ngombe_task.ps1` (task "Ngombe line watcher",
at logon and every 5 min, single instance); the standby tells Chris by ntfy when its heartbeat is older than 5 min.

**Anyone can use the line (7 Nov 2026, Chris: "You can't just receive messages from linked numbers").** A number with no
profile that sends cattle content (a report, a photo, "new animal X", "my animals") gets a profile on the spot
(`created_via 'line'`, an auth user `<number>@line.ngombe.invalid`, name from WhatsApp, phone tied) and a one-line welcome
that names the terms. Animals are registered from the line with class 'unknown' (the app sets the rest); an unknown name in
a report ("Chipego: limping") is filed and the person is asked to reply YES to register it. When the same person later ties
the number in the app, `cattle.merge_line_profile` moves animals, photos and events into the app profile and deletes the
line profile (`002_line_profiles.sql`; the bind function and the watcher both call it). Strangers who write anything else
are the standby session's, as before. Meta can deliver a message minutes after its stamp (Matthew's code: 12:28 sent,
12:35 delivered); the watcher reads a 90-minute window and logs "late delivery".

**The model answers (7 Nov 2026, 13:20).** Chris: "Those canned messages can be scrapped ... The triage needs to be smarter
than that, more natural." `tools/zamai_line/ngombe_brain.py`: one Claude Sonnet 5.5 call per message from a Ng'ombe user
(low effort, strict tools file_event / file_event_all / register_animal / set_status / attach_photo / tell_chris, the
system prompt cached), with the profile, herd and notes, last entries, the last twelve thread messages, the translator's
reading of Tonga, and the photo itself. The model writes every word; the watcher executes the tools against the backend.
Measured on the first three calls: 1,100 to 1,450 uncached input tokens, 2,016 cached, 100 to 135 output, about 7 s per
answer, about US$0.004 per message. Key: ANTHROPIC_API_KEY in ZamaiPort/.env.local (read per call). When the call fails
the standby session is woken with the number. A code is still tied deterministically before the model greets. Strangers
without a profile stay with the standby session. NGOMBE_MODEL switches the model.

**Admin view (7 Nov 2026, Chris: "Yes, we need an admin view").** `netlify/functions/ngombe-admin.mjs`, served at
https://ngombe.zamai.pro/cattle-demo/admin (also /admin-ngombe on zamai.pro), behind DESK_KEY: first visit with `?k=<key>`
sets an HttpOnly cookie for 30 days. All profiles with phone, origin (app or line), animals and last entry; a person's
page with animals, photos (signed URLs), entries with the translator's reading, and their conversation on the line;
"Close this profile" (type the name): storage objects, rows through `cattle.close_profile` (003_admin.sql, which keeps
one row in cattle.erasures with counts and no personal data) and the auth user. Never linked from the public site.

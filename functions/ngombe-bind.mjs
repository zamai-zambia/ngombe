// Tie a phone number to a Ng'ombe profile through the Zamai WhatsApp line (7 Nov 2026).
// The app shows a six-digit code; the person sends "Ngombe <code>" to the line from their own phone. This function
// looks for that message in the line's table (zamai_messages, in the Yumi project, inbound only, last 15 minutes),
// checks the code belongs to the profile that asks, and writes the number on the profile with the service role of
// the self-hosted backend. Nothing else can set profiles.phone.
//   POST /cattle-demo/bind {code, uid} -> {ok, phone} | {ok:false, message}
// Env: SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY (the Yumi project, read-only use here),
//      NGOMBE_SUPABASE_URL + NGOMBE_SUPABASE_SERVICE_ROLE_KEY (the backend on our machine; the URL may be looked up
//      from the api-url blob when the env is empty).
import { getStore } from '@netlify/blobs';
const H = { 'Access-Control-Allow-Origin': 'https://ngombe.zamai.pro', 'Access-Control-Allow-Headers': 'Content-Type', 'Cache-Control': 'no-store', 'Content-Type': 'application/json' };
const json = (code, obj) => new Response(JSON.stringify(obj), { status: code, headers: H });

export default async (req) => {
  if (req.method === 'OPTIONS') return new Response('', { status: 204, headers: H });
  if (req.method !== 'POST') return json(405, { ok: false, message: 'method' });
  let b; try { b = await req.json(); } catch { return json(400, { ok: false, message: 'bad request' }); }
  const code = String(b.code || '').trim(), uid = String(b.uid || '').trim();
  if (!/^[0-9]{6}$/.test(code) || !/^[0-9a-f-]{36}$/.test(uid)) return json(400, { ok: false, message: 'bad code' });

  let NURL = process.env.NGOMBE_SUPABASE_URL, NKEY = process.env.NGOMBE_SUPABASE_SERVICE_ROLE_KEY;
  if (!NURL) { const cur = await getStore('ngombe-api').get('current', { type: 'json' }); NURL = cur && cur.url; }
  if (!NURL || !NKEY) return json(503, { ok: false, message: 'The records service is not reachable right now.' });
  const nh = { apikey: NKEY, Authorization: 'Bearer ' + NKEY, 'Content-Type': 'application/json', 'Accept-Profile': 'cattle', 'Content-Profile': 'cattle' };

  // the code must exist, be unused, be younger than 15 minutes and belong to this profile
  const since = new Date(Date.now() - 15 * 60e3).toISOString();
  const c = await (await fetch(`${NURL}/rest/v1/phone_codes?code=eq.${code}&profile=eq.${uid}&used_at=is.null&created_at=gte.${since}&select=code`, { headers: nh })).json();
  if (!Array.isArray(c) || !c.length) return json(200, { ok: false, message: 'That code is not valid any more. Make a new one.' });

  // the message on the Zamai line
  const YURL = process.env.SUPABASE_URL, YKEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!YURL || !YKEY) return json(503, { ok: false, message: 'The line is not reachable right now.' });
  const yh = { apikey: YKEY, Authorization: 'Bearer ' + YKEY };
  // inbound from any number; or, when the message was sent from the line's own phone (the line's owner testing), the
  // line's own number: that row is recorded as outbound to itself
  const m = await (await fetch(`${YURL}/rest/v1/zamai_messages?created_at=gte.${since}&body=ilike.*${code}*&select=counterparty,body,created_at,direction&order=created_at.desc&limit=5`, { headers: yh })).json();
  const LINE = '260776621255';
  const hit = Array.isArray(m) ? m.find((x) => (x.direction === 'in' && /^260[0-9]{9}$/.test(String(x.counterparty || ''))) || (x.direction === 'out' && String(x.counterparty) === LINE)) : null;
  if (!hit) return json(200, { ok: false, message: 'Not arrived yet. Send the code from your phone to the Zamai line, then tap again.' });
  const phone = String(hit.counterparty);

  // one number, one profile
  const other = await (await fetch(`${NURL}/rest/v1/profiles?phone=eq.${phone}&id=neq.${uid}&select=id,created_via`, { headers: nh })).json();
  let merged = false;
  if (Array.isArray(other) && other.length) {
    // a profile the line made for this number from WhatsApp alone: the app profile absorbs it (002_line_profiles.sql)
    if (other[0].created_via !== 'line') return json(200, { ok: false, message: 'That number is already tied to another profile. Write to the line if that is wrong.' });
    const r = await fetch(`${NURL}/rest/v1/rpc/merge_line_profile`, { method: 'POST', headers: nh, body: JSON.stringify({ line_profile: other[0].id, app_profile: uid }) });
    if (!r.ok) return json(500, { ok: false, message: 'Could not merge the records made on the line.' });
    merged = true;
  }

  const u = await fetch(`${NURL}/rest/v1/profiles?id=eq.${uid}`, { method: 'PATCH', headers: { ...nh, Prefer: 'return=minimal' }, body: JSON.stringify({ phone, phone_bound_at: new Date().toISOString() }) });
  if (!u.ok) return json(500, { ok: false, message: 'Could not save the number.' });
  await fetch(`${NURL}/rest/v1/phone_codes?code=eq.${code}`, { method: 'PATCH', headers: { ...nh, Prefer: 'return=minimal' }, body: JSON.stringify({ used_at: new Date().toISOString() }) });
  await fetch(`${NURL}/rest/v1/events`, { method: 'POST', headers: { ...nh, Prefer: 'return=minimal' }, body: JSON.stringify({ owner: uid, animal: null, kind: 'note', data: { note: 'phone tied through the Zamai line' }, source: 'whatsapp' }) });
  return json(200, { ok: true, phone, merged });
};
export const config = { path: ['/cattle-demo/bind', '/bind-ngombe'] };

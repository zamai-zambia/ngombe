// Ng'ombe admin view (7 Nov 2026; Chris: "Yes, we need an admin view"). Chris's private view of the records service:
// every profile with its herd, each person's animals, entries, photos and their conversation on the Zamai line, and the
// one action the app cannot do itself: closing a profile (erasure). Served only by this function, behind DESK_KEY, as the
// Forecast Desk is; nothing of it is in site/. Reads the backend with the service role (NGOMBE_SUPABASE_SERVICE_ROLE_KEY,
// URL from the api-url blob) and the line's table in the Yumi project (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY).
//   GET  /cattle-demo/admin?k=<DESK_KEY>      first visit sets the cookie; then /cattle-demo/admin
//   GET  /cattle-demo/admin?p=<profile id>    one person
//   POST /cattle-demo/admin  p=<id>&confirm=<name>&why=...   closes the profile: storage objects, rows, auth user
import { getStore } from '@netlify/blobs';
import { timingSafeEqual } from 'node:crypto';

const LINE = '260776621255';
const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const html = (body, status = 200, extra = {}) => new Response(body, { status, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex', ...extra } });
const sameKey = (a, b) => { const x = Buffer.from(String(a || '')), y = Buffer.from(String(b || '')); return x.length === y.length && x.length > 0 && timingSafeEqual(x, y); };
const CSS = `body{font:15px/1.5 -apple-system,"Segoe UI",Roboto,Arial,sans-serif;margin:0;background:#f6f5f1;color:#1b1b1b}
header{background:#1f3b2d;color:#fff;padding:12px 20px;display:flex;justify-content:space-between;align-items:baseline}header a{color:#fff;text-decoration:none}
main{max-width:1080px;margin:0 auto;padding:16px 20px 60px}h1{font-size:18px;margin:0}h2{font-size:17px;margin:26px 0 8px;color:#1f3b2d}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #e5e2da;vertical-align:top}th{background:#eeece5;font-weight:600}
.muted{color:#6b6b6b}.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:12px;background:#e8efe9;color:#1f3b2d}.pill.line{background:#f1e4cc;color:#6a4b00}
.chat{max-width:720px}.msg{margin:4px 0;padding:6px 10px;border-radius:8px;background:#fff;border:1px solid #e5e2da}.msg.in{border-color:#c9d9ce}.msg.out{background:#eef3ef}.msg small{display:block;color:#6b6b6b;font-size:12px}
.photos{display:flex;flex-wrap:wrap;gap:8px}.photos img{height:140px;border-radius:6px;border:1px solid #ddd}
.danger{border:1px solid #b56b2b;background:#fff7ef;padding:12px 14px;border-radius:8px;max-width:560px}button{font:inherit;padding:6px 12px;border-radius:6px;border:1px solid #1f3b2d;background:#1f3b2d;color:#fff}button.warn{background:#b56b2b;border-color:#b56b2b}
input[type=text]{font:inherit;padding:6px 8px;border:1px solid #bbb;border-radius:6px;width:100%;max-width:320px}a{color:#1f3b2d}`;

async function backend() {
  let url = process.env.NGOMBE_SUPABASE_URL;
  if (!url) { const cur = await getStore('ngombe-api').get('current', { type: 'json' }); url = cur && cur.url; }
  const key = process.env.NGOMBE_SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error('backend not configured');
  const h = { apikey: key, Authorization: 'Bearer ' + key, 'Content-Type': 'application/json', 'Accept-Profile': 'cattle', 'Content-Profile': 'cattle' };
  const get = async (q) => { const r = await fetch(`${url}/rest/v1/${q}`, { headers: h }); if (!r.ok) throw new Error(`backend ${r.status} on ${q.split('?')[0]}: ${(await r.text()).slice(0, 200)}`); return r.json(); };
  const post = async (q, body) => { const r = await fetch(`${url}/rest/v1/${q}`, { method: 'POST', headers: h, body: JSON.stringify(body) }); if (!r.ok) throw new Error(`backend ${r.status} on ${q}: ${(await r.text()).slice(0, 200)}`); const t = await r.text(); return t ? JSON.parse(t) : null; };
  const sign = async (path) => { const r = await fetch(`${url}/storage/v1/object/sign/cattle-photos/${path}`, { method: 'POST', headers: h, body: JSON.stringify({ expiresIn: 900 }) }); if (!r.ok) return null; const j = await r.json(); return j.signedURL ? `${url}/storage/v1${j.signedURL}` : null; };
  return { url, key, h, get, post, sign };
}

async function lineMessages(phone, limit = 40) {
  const u = process.env.SUPABASE_URL, k = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!u || !k || !phone) return [];
  const r = await fetch(`${u}/rest/v1/zamai_messages?counterparty=eq.${phone}&select=created_at,direction,msg_type,body&order=created_at.desc&limit=${limit}`, { headers: { apikey: k, Authorization: 'Bearer ' + k } });
  if (!r.ok) return [];
  return (await r.json()).reverse();
}

const hm = (iso) => { const d = new Date(iso); if (isNaN(d)) return '?'; return d.toLocaleString('en-GB', { timeZone: 'Africa/Lusaka', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); };

async function listPage(B) {
  const profiles = await B.get('profiles?select=id,name,place,district,phone,created_via,terms_version,created_at&order=created_at.desc');
  const animals = await B.get('animals?select=owner,status');
  const last = await B.get('events?select=owner,at,kind,source&order=id.desc&limit=400');
  const erasures = await B.get('erasures?select=at,animals,events,photos,note&order=id.desc&limit=10');
  const count = {}; for (const a of animals) { count[a.owner] = count[a.owner] || { alive: 0, all: 0 }; count[a.owner].all++; if (a.status === 'alive') count[a.owner].alive++; }
  const lastBy = {}; for (const e of last) if (!lastBy[e.owner]) lastBy[e.owner] = e;
  const rows = profiles.map((p) => `<tr><td><a href="?p=${p.id}">${esc(p.name)}</a><br><span class="muted">${esc(p.place || '')}${p.place && p.district ? ', ' : ''}${esc(p.district || '')}</span></td>
    <td>${p.phone ? esc(p.phone) : '<span class="muted">not tied</span>'}</td><td><span class="pill${p.created_via === 'line' ? ' line' : ''}">${p.created_via === 'line' ? 'from the line' : 'app'}</span>${p.terms_version ? '' : ' <span class="muted">no terms</span>'}</td>
    <td>${count[p.id] ? `${count[p.id].alive} live / ${count[p.id].all}` : '0'}</td><td>${lastBy[p.id] ? `${hm(lastBy[p.id].at)} <span class="muted">${esc(lastBy[p.id].kind)} via ${esc(lastBy[p.id].source)}</span>` : '<span class="muted">none</span>'}</td><td class="muted">${hm(p.created_at)}</td></tr>`).join('');
  const er = erasures.length ? `<h2>Closed profiles</h2><table><tr><th>When</th><th>Animals</th><th>Entries</th><th>Photos</th><th>Why</th></tr>${erasures.map((e) => `<tr><td>${hm(e.at)}</td><td>${e.animals}</td><td>${e.events}</td><td>${e.photos}</td><td>${esc(e.note || '')}</td></tr>`).join('')}</table>` : '';
  return `<h1>Ng'ombe: ${profiles.length} profile${profiles.length === 1 ? '' : 's'}, ${animals.length} animal${animals.length === 1 ? '' : 's'}</h1>
  <table><tr><th>Person</th><th>Phone</th><th>Made</th><th>Animals</th><th>Last entry</th><th>Profile since</th></tr>${rows || '<tr><td colspan="6" class="muted">no profiles yet</td></tr>'}</table>${er}
  <p class="muted">Backend ${esc(B.url)}. Times in Lusaka time. The line's conversations are on each person's page.</p>`;
}

async function personPage(B, id) {
  const [p] = await B.get(`profiles?id=eq.${id}&select=*`);
  if (!p) return '<h1>No such profile</h1>';
  const animals = await B.get(`animals?owner=eq.${id}&select=*&order=created_at`);
  const events = await B.get(`events?owner=eq.${id}&select=id,animal,kind,at,data,source,created_at&order=id.desc&limit=200`);
  const photos = await B.get(`photos?owner=eq.${id}&select=animal,path,kind,taken_at&order=created_at.desc`);
  const names = Object.fromEntries(animals.map((a) => [a.id, a.name]));
  const shots = await Promise.all(photos.map(async (ph) => ({ ...ph, url: await B.sign(ph.path) })));
  const linePhotos = events.filter((e) => e.data && e.data.photo && !photos.some((ph) => ph.path === e.data.photo));
  const lineShots = await Promise.all(linePhotos.map(async (e) => ({ animal: e.animal, path: e.data.photo, kind: 'line', taken_at: e.at, url: await B.sign(e.data.photo) })));
  const allShots = [...shots, ...lineShots];
  const chat = await lineMessages(p.phone);
  const evRows = events.map((e) => { const d = e.data || {}; const what = d.text || d.note || (d.kg ? d.kg + ' kg' : '') || (d.photo ? 'photo' : ''); return `<tr><td>${hm(e.at)}</td><td>${e.animal ? esc(names[e.animal] || '?') : '<span class="muted">herd</span>'}</td><td>${esc(e.kind)}</td><td>${esc(what)}${d.text_en ? `<br><span class="muted">read as: ${esc(d.text_en)}</span>` : ''}</td><td class="muted">${esc(e.source)}</td></tr>`; }).join('');
  const anRows = animals.map((a) => `<tr><td><b>${esc(a.name)}</b></td><td>${esc(a.class)} ${a.sex ? '(' + a.sex + ')' : ''}</td><td>${esc(a.tag || '')}</td><td>${a.dob ? esc(a.dob) + ' <span class="muted">' + esc(a.dob_kind || '') + '</span>' : (a.dob_year ? a.dob_year + ' <span class="muted">teeth</span>' : '')}</td><td>${esc(a.colour || '')}</td><td>${esc(a.status)}</td><td>${esc(a.notes || '')}</td></tr>`).join('');
  const chatHtml = chat.length ? chat.map((m) => `<div class="msg ${m.direction}"><small>${hm(m.created_at)} ${m.direction === 'in' ? esc(p.name) : 'line'}${m.msg_type && m.msg_type !== 'text' ? ' (' + esc(m.msg_type) + ')' : ''}</small>${esc(m.body || '')}</div>`).join('') : '<p class="muted">no messages on the line from this number</p>';
  return `<p><a href="?">All profiles</a></p><h1>${esc(p.name)} <span class="pill${p.created_via === 'line' ? ' line' : ''}">${p.created_via === 'line' ? 'from the line' : 'app'}</span></h1>
  <p>${esc(p.place || '')}${p.place && p.district ? ', ' : ''}${esc(p.district || '')} · ${esc(p.role)} · phone ${p.phone ? esc(p.phone) + ' (tied ' + hm(p.phone_bound_at) + ')' : '<span class="muted">not tied</span>'} · terms ${p.terms_version ? esc(p.terms_version) + ' accepted ' + hm(p.terms_accepted_at) : '<span class="muted">not accepted</span>'} · profile since ${hm(p.created_at)}<br><span class="muted">${p.id}</span></p>
  <h2>Animals (${animals.length})</h2><table><tr><th>Name</th><th>Class</th><th>Tag</th><th>Born</th><th>Colour</th><th>Status</th><th>Notes</th></tr>${anRows || '<tr><td colspan="7" class="muted">none</td></tr>'}</table>
  <h2>Photos (${allShots.length})</h2><div class="photos">${allShots.map((s) => s.url ? `<a href="${s.url}" target="_blank"><img src="${s.url}" alt="" title="${esc(names[s.animal] || 'herd')} · ${esc(s.kind)} · ${hm(s.taken_at)}"></a>` : '').join('') || '<span class="muted">none</span>'}</div>
  <h2>Entries (${events.length})</h2><table><tr><th>When</th><th>Animal</th><th>Kind</th><th>What</th><th>Via</th></tr>${evRows || '<tr><td colspan="5" class="muted">none</td></tr>'}</table>
  <h2>The line</h2><div class="chat">${chatHtml}</div>
  <h2>Close this profile</h2><div class="danger"><p>Removes the person's animals, entries, photos and the login, and keeps one row saying that a profile with ${animals.length} animal${animals.length === 1 ? '' : 's'} and ${events.length} entr${events.length === 1 ? 'y' : 'ies'} was closed. Cannot be undone. Type the name exactly to confirm.</p>
  <form method="post"><input type="hidden" name="p" value="${p.id}"><p><input type="text" name="confirm" placeholder="${esc(p.name)}" autocomplete="off"></p><p><input type="text" name="why" placeholder="why (optional)"></p><button class="warn">Close the profile</button></form></div>`;
}

async function closeProfile(B, id, confirm, why) {
  const [p] = await B.get(`profiles?id=eq.${id}&select=id,name`);
  if (!p) return '<h1>No such profile</h1>';
  if ((confirm || '').trim() !== p.name) return `<h1>Not closed</h1><p>The name typed did not match. <a href="?p=${id}">Back</a></p>`;
  // storage first: list every object under the profile's folder (app photos and line photos), then delete them
  const listed = await fetch(`${B.url}/storage/v1/object/list/cattle-photos`, { method: 'POST', headers: B.h, body: JSON.stringify({ prefix: id + '/', limit: 1000, offset: 0 }) });
  const folders = listed.ok ? await listed.json() : [];
  const paths = [];
  for (const f of folders) {
    if (f.id) { paths.push(`${id}/${f.name}`); continue; }
    const sub = await fetch(`${B.url}/storage/v1/object/list/cattle-photos`, { method: 'POST', headers: B.h, body: JSON.stringify({ prefix: `${id}/${f.name}/`, limit: 1000, offset: 0 }) });
    for (const o of (sub.ok ? await sub.json() : [])) if (o.id) paths.push(`${id}/${f.name}/${o.name}`);
  }
  if (paths.length) await fetch(`${B.url}/storage/v1/object/cattle-photos`, { method: 'DELETE', headers: B.h, body: JSON.stringify({ prefixes: paths }) });
  const counts = await B.post('rpc/close_profile', { p: id, why: (why || '').slice(0, 200) || null });
  const au = await fetch(`${B.url}/auth/v1/admin/users/${id}`, { method: 'DELETE', headers: { apikey: B.key, Authorization: 'Bearer ' + B.key } });
  return `<h1>Closed: ${esc(p.name)}</h1><p>${counts.animals} animal(s), ${counts.events} entr(ies), ${counts.photos} photo row(s), ${paths.length} stored file(s) removed; login ${au.ok ? 'removed' : 'not removed (' + au.status + ')'}.</p><p><a href="?">All profiles</a></p>`;
}

export default async (req) => {
  const url = new URL(req.url);
  const want = process.env.DESK_KEY;
  if (!want) return html('<p>DESK_KEY is not set.</p>', 503);
  const cookie = (req.headers.get('cookie') || '').split(';').map((s) => s.trim()).find((s) => s.startsWith('ngadmin='));
  const given = url.searchParams.get('k') || (cookie ? decodeURIComponent(cookie.slice(8)) : '');
  if (!sameKey(given, want)) return html('<p>Private.</p>', 403);
  const setCookie = url.searchParams.get('k') ? { 'Set-Cookie': `ngadmin=${encodeURIComponent(want)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000` } : {};
  let body;
  try {
    const B = await backend();
    if (req.method === 'POST') {
      const form = await req.formData();
      body = await closeProfile(B, String(form.get('p') || ''), String(form.get('confirm') || ''), String(form.get('why') || ''));
    } else if (url.searchParams.get('p')) {
      body = await personPage(B, url.searchParams.get('p'));
    } else {
      body = await listPage(B);
    }
  } catch (e) {
    body = `<h1>Not reachable</h1><p>${esc(e.message)}</p><p class="muted">The backend runs on our machine behind the tunnel; if the tunnel is down, start it and reload.</p>`;
  }
  return html(`<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Ng'ombe admin</title><style>${CSS}</style></head><body><header><a href="?"><b>Ng'ombe</b> admin</a><span class="muted" style="color:#cfd9d2">private</span></header><main>${body}</main></body></html>`, 200, setCookie);
};
export const config = { path: ['/cattle-demo/admin', '/admin-ngombe'] };

// Where is the Ng'ombe backend right now? (7 Nov 2026)
// The database runs on our machine behind a Cloudflare quick tunnel whose address changes on restart. The machine
// posts the current address here (header x-desk-key = DESK_KEY); the app asks for it on load.
//   GET  /cattle-demo/api-url                 -> { url, at }
//   POST /cattle-demo/api-url {url, anon?}, x-desk-key -> stores it (anon = the public anon key of that backend)
import { getStore } from '@netlify/blobs';
const H = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, x-desk-key', 'Cache-Control': 'no-store', 'Content-Type': 'application/json' };
export default async (req) => {
  if (req.method === 'OPTIONS') return new Response('', { status: 204, headers: H });
  const store = getStore('ngombe-api');
  if (req.method === 'POST') {
    if (!process.env.DESK_KEY || req.headers.get('x-desk-key') !== process.env.DESK_KEY) return new Response('{"error":"forbidden"}', { status: 403, headers: H });
    let b; try { b = await req.json(); } catch { return new Response('{"error":"bad request"}', { status: 400, headers: H }); }
    const url = String(b.url || '').trim();
    if (!/^https:\/\/[a-z0-9.-]+(\.trycloudflare\.com|\.zamai\.pro)$/.test(url)) return new Response('{"error":"not a tunnel address"}', { status: 400, headers: H });
    const anon = String(b.anon || '').trim();
    if (anon && !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(anon)) return new Response('{"error":"bad anon key"}', { status: 400, headers: H });
    const prev = (await store.get('current', { type: 'json' })) || {};
    await store.setJSON('current', { url, anon: anon || prev.anon || null, at: new Date().toISOString() });
    return new Response(JSON.stringify({ ok: true, url }), { status: 200, headers: H });
  }
  const cur = (await store.get('current', { type: 'json' })) || null;
  return new Response(JSON.stringify(cur || { url: null }), { status: 200, headers: H });
};
export const config = { path: ['/cattle-demo/api-url', '/api-url-ngombe'] };

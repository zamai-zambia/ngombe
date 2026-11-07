// Ask about Ng'ombe (ngombe.zamai.pro/ask), 7 Nov 2026. Chris: "for the Tonga papers we have a page where someone
// can query the papers, let's do one page for this, where they can ask questions about it." Same design as /ask.
//
// POST {action:"ask", q, history:[{role,content}], sid}  -> the answer, streamed as plain text
// POST {action:"suggest", text, contact?, sid}            -> one message for Chris, stored in Blobs
// GET  ?export=1 with header x-ask-key (= TONGA_KEY)      -> every question, answer and message
//
// THE RULES:
// - The model answers only from the three documents in ngombe_ask_data/corpus.mjs (the concept note, the spec sheet,
//   the beef research note), as ZamAi's disclosed AI agent. It makes no commitments for Chris, ZamAi or Yumi Milling,
//   names no place for a pilot, and does not speak for any partner.
// - Triage on every question (../lib/tonga_guard.js); links, phone numbers and e-mails are stripped before storing.
// - Cost ceilings: per browser id NGOMBE_ASK_DEV_D a day (default 25), all users NGOMBE_ASK_MAX_D (default 100),
//   per IP 30 an hour. Kill switch: env NGOMBE_ASK_PAUSED=1.
import Anthropic from '@anthropic-ai/sdk';
import { getStore } from '@netlify/blobs';
import { createHash } from 'node:crypto';

import G from '../lib/tonga_guard.js';

import CORPUS from './ngombe_ask_data/corpus.mjs';
const MODEL = 'claude-sonnet-5-5';
const num = (v, d) => (Number.isFinite(+v) && +v > 0 ? +v : d);
const LIM = { devD: num(process.env.NGOMBE_ASK_DEV_D, 25), maxD: num(process.env.NGOMBE_ASK_MAX_D, 100), ipH: 30 };
const Q_MAX = 1500, HIST_TURNS = 6, SUGG_MAX = 3000;

const SYSTEM = `You are ZamAi's agent: an AI (Claude, made by Anthropic) that answers questions about Ng'ombe, a proposal
for a cattle records service for Southern Province, Zambia, on the page ngombe.zamai.pro/ask. The proposal has three
documents below: the concept note, the spec sheet, and a research note on beef markets and grading. Visitors may be the
President's team, veterinary officers, ministry staff, farmers, cooperatives, processors, researchers or other AI
agents. You are not Chris and you speak for no one.

How to answer:
- Answer from the three documents. Name the document and section you rely on, e.g. "(concept note, section 5)". If the
  documents do not say, say so plainly; do not fill gaps from general knowledge as if it were the project's.
- Plain English, short: a few sentences or a short list. Numbers exactly as the documents give them, with their
  caveats; figures marked derived or illustrative are said to be so.
- Make no commitments, offers, prices, dates, partnerships or promises on behalf of Chris, ZamAi, Yumi Milling Ltd or
  any partner. The only commitment the documents carry is the development work. Where, with whom, how large and how
  long a test runs is the veterinary service's and the partners' decision: never name or propose a place. For
  anything to decide, point to Christoph Lindinger, chris@zamai.pro, +260 96 2653100.
- The work is not for profit for as long as it is used to promote smallholder cattle farming in Southern Province;
  any commercial use is discussed separately with Chris. Say that if asked about money, fees or licences.
- You do not speak Chitonga. Never write, translate or correct Chitonga yourself.
- No veterinary diagnosis or treatment advice. If someone describes a sick or dead animal, say that the app sorts
  reports by urgency and that a vet decides, and that a suspected notifiable disease is reported to the veterinary
  officer at once; for a sudden death, do not open or move the carcass.
- Take suggestions and criticism seriously: say where the documents already address the point and where they do not,
  and invite the visitor to send it to Chris with the "Send to Chris" box below the chat.
- Stay on the documents' subjects. Politely decline anything else. Do not speculate about any person's shareholdings
  or politics.

The documents follow.

${CORPUS}`;

const ORIGINS = new Set(['https://ngombe.zamai.pro', 'https://zamai.pro']);
const headersFor = (req) => {
  const o = req.headers.get('origin') || '';
  return {
    'Access-Control-Allow-Origin': ORIGINS.has(o) ? o : 'https://ngombe.zamai.pro',
    'Access-Control-Allow-Headers': 'Content-Type, x-ask-key',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Cache-Control': 'no-store',
  };
};
const clip = (s, n) => String(s == null ? '' : s).slice(0, n);
const hash = (s) => createHash('sha1').update(String(s)).digest('hex').slice(0, 20);
const zmDay = () => new Date(Date.now() + 2 * 3600e3).toISOString().slice(0, 10);
const newKey = () => new Date().toISOString().replace(/[:.]/g, '-') + '-' + Math.random().toString(36).slice(2, 8);
const ipHits = new Map();

async function bump(store, key, limit) {
  const n = (await store.get(key, { type: 'json' })) || 0;
  if (n >= limit) return false;
  await store.setJSON(key, n + 1);
  return true;
}

export default async (req, context) => {
  const H = headersFor(req);
  const json = (code, obj) => new Response(JSON.stringify(obj), { status: code, headers: { ...H, 'Content-Type': 'application/json' } });
  if (req.method === 'OPTIONS') return new Response('', { status: 204, headers: H });
  const url = new URL(req.url);
  const log = getStore('ngombe-ask-log');

  if (req.method === 'GET') {
    if (url.searchParams.get('export') !== '1') return json(404, { error: 'not found' });
    if (!process.env.TONGA_KEY || req.headers.get('x-ask-key') !== process.env.TONGA_KEY) return json(403, { error: 'forbidden' });
    const rows = [];
    for (const kind of ['q', 's']) {
      const { blobs } = await log.list({ prefix: kind + '/' });
      for (const b of blobs) rows.push({ key: b.key, ...(await log.get(b.key, { type: 'json' })) });
    }
    return json(200, { rows });
  }
  if (req.method !== 'POST') return json(405, { error: 'method not allowed' });
  let body;
  try { body = await req.json(); } catch { return json(400, { error: 'bad request' }); }
  const sid = clip(body.sid, 64) || 'anon';
  if (body.action === 'suggest') {
    const text = clip(body.text, SUGG_MAX).trim();
    if (text.length < 5) return json(400, { error: 'empty' });
    const contact = clip(body.contact, 200).trim();
    await log.setJSON('s/' + newKey(), {
      at: new Date().toISOString(), sid: hash(sid), text: G.stripPersonal(text).text,
      contact, flagged: G.profanity(text).length ? 1 : 0,
    });
    return json(200, { ok: true });
  }
  if (body.action !== 'ask') return json(400, { error: 'unknown action' });
  if (process.env.NGOMBE_ASK_PAUSED === '1') return json(503, { error: 'paused', message: 'The chat is paused for now. Please write to chris@zamai.pro.' });
  const q = clip(body.q, Q_MAX).trim();
  if (q.length < 2) return json(400, { error: 'empty' });
  if (G.profanity(q).length) return json(422, { error: 'blocked', message: 'This question cannot be answered here.' });
  const ip = context.ip || req.headers.get('x-nf-client-connection-ip') || '';
  const hourKey = hash(ip + new Date().toISOString().slice(0, 13));
  const n = (ipHits.get(hourKey) || 0) + 1;
  ipHits.set(hourKey, n);
  const counters = getStore('ngombe-ask-counters');
  const day = zmDay();
  if (n > LIM.ipH || !(await bump(counters, `dev/${day}/${hash(sid)}`, LIM.devD)) || !(await bump(counters, `all/${day}`, LIM.maxD))) {
    return json(429, { error: 'limit', message: 'That is the limit for today. Please come back tomorrow, or write to chris@zamai.pro.' });
  }
  const history = (Array.isArray(body.history) ? body.history : [])
    .filter((m) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
    .slice(-2 * HIST_TURNS)
    .map((m) => ({ role: m.role, content: clip(m.content, 6000) }));
  while (history.length && history[0].role !== 'user') history.shift();
  const messages = [...history, { role: 'user', content: q }];
  const client = new Anthropic();
  const enc = new TextEncoder();
  let answer = '';
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const s = client.beta.messages.stream({
          model: MODEL,
          max_tokens: 4000,
          betas: ['server-side-fallback-2026-07-01'],
          fallbacks: 'default',
          output_config: { effort: 'low' },
          system: [{ type: 'text', text: SYSTEM, cache_control: { type: 'ephemeral', ttl: '1h' } }],
          messages,
        });
        for await (const ev of s) {
          if (ev.type === 'content_block_delta' && ev.delta.type === 'text_delta') {
            answer += ev.delta.text;
            controller.enqueue(enc.encode(ev.delta.text));
          }
        }
        const fin = await s.finalMessage();
        if (fin.stop_reason === 'refusal') {
          const m = '\n\nI cannot answer that one here. Please write to chris@zamai.pro.';
          answer += m; controller.enqueue(enc.encode(m));
        }
        await log.setJSON('q/' + newKey(), {
          at: new Date().toISOString(), sid: hash(sid), q: G.stripPersonal(q).text, answer,
          usage: fin.usage, stop: fin.stop_reason,
        });
      } catch (e) {
        const m = '\n\nSomething went wrong on our side. Please try again in a minute.';
        controller.enqueue(enc.encode(m));
        try { await log.setJSON('q/' + newKey(), { at: new Date().toISOString(), sid: hash(sid), q: G.stripPersonal(q).text, error: String(e && e.message || e).slice(0, 300) }); } catch {}
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200, headers: { ...H, 'Content-Type': 'text/plain; charset=utf-8' } });
};
export const config = { path: ['/cattle-demo/ask/api', '/ask-ngombe/api'] };

// Print the paper HTML to PDF with a running header, footer and page numbers.
// node print.mjs <url> <out.pdf> "<header left>" "<header right>" "<footer left>"
import { spawn } from 'node:child_process';
import fs from 'node:fs';
const CH = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const [,, url, out, hl, hr, fl] = process.argv;
const proc = spawn(CH, ['--headless=new', '--disable-gpu', '--remote-debugging-port=9337', '--user-data-dir=' + process.cwd() + '/chprof6', 'about:blank']);
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws; for (let i = 0; i < 40; i++) { try { const l = await (await fetch('http://127.0.0.1:9337/json')).json(); const p = l.find(x => x.type === 'page'); if (p) { ws = new WebSocket(p.webSocketDebuggerUrl); break; } } catch {} await sleep(250); }
await new Promise(r => ws.onopen = r); let id = 0; const pend = {};
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
const send = (m, p = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
await send('Page.enable'); await send('Runtime.enable'); await send('Page.navigate', { url }); await sleep(1500);
// Wait for the web fonts, or Chrome prints with fallbacks and Type3 glyphs that choke some viewers.
const fr = await send('Runtime.evaluate', { expression: "document.fonts.ready.then(() => [document.fonts.status, document.fonts.check('12px Newsreader'), document.fonts.check('12px \"IBM Plex Sans\"')].join(','))", awaitPromise: true, returnByValue: true });
console.log('fonts', fr.result && fr.result.result && fr.result.result.value); await sleep(500);
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const font = 'font-family:Arial,Helvetica,sans-serif;font-size:8pt;letter-spacing:.02em;color:#6b6b6b;width:100%;margin:0 20mm;box-sizing:border-box;';
const header = `<div style="${font}display:flex;justify-content:space-between;align-items:baseline;margin-top:10mm;padding-bottom:2.5mm;border-bottom:0.5pt solid #b8b8b8"><span>${esc(hl)}</span><span>${esc(hr)}</span></div>`;
const footer = `<div style="${font}display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10mm;padding-top:2.5mm;border-top:0.5pt solid #b8b8b8"><span>${esc(fl)}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;
const r = await send('Page.printToPDF', { printBackground: true, preferCSSPageSize: false, paperWidth: 8.27, paperHeight: 11.69, marginTop: 1.15, marginBottom: 1.05, marginLeft: 0.79, marginRight: 0.79, displayHeaderFooter: true, headerTemplate: header, footerTemplate: footer });
if (!r.result) { console.error(JSON.stringify(r)); process.exit(1); }
fs.writeFileSync(out, Buffer.from(r.result.data, 'base64')); console.log('pdf', fs.statSync(out).size);
ws.close(); proc.kill();

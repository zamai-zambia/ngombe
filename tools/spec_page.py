# Build site/cattle-demo/spec-sheet.html (outward copy) from internal/cattle/CATTLE_SPEC_SHEET.md
import re, sys, html
src, out = sys.argv[1], sys.argv[2]
md = open(src, encoding='utf-8').read()
# outward edits: no internal file names, no named translator
md = md.replace("Companion to the demo at zamai.pro/cattle-demo/ and to\n`CATTLE_APP_SPEC.md` (the product spec) and `CATTLE_PROGRAMME_CONCEPT.md` (the programme).", "Companion to the demo at zamai.pro/cattle-demo/.")
md = md.replace("Matthew Sakala is translating the demo's 300 lines now.", "A Tonga speaker is translating the demo's 300 lines now.")
md = md.replace("Changes: v0, 6 Nov 2026, from the product spec, the programme concept and the demo as of this evening.", "Changes: v0, 6 November 2026. Corrections to chris@zamai.pro.")
md = re.sub(r"`([^`]+)`", r"\1", md)
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t
lines = md.split('\n'); outl = []; i = 0; inlist = None
def close():
    global inlist
    if inlist: outl.append('</%s>' % inlist); inlist = None
while i < len(lines):
    l = lines[i]
    if l.startswith('# '): close(); outl.append('<h1>%s</h1>' % inline(l[2:])); i += 1; continue
    if l.startswith('## '): close(); outl.append('<h2>%s</h2>' % inline(l[3:])); i += 1; continue
    if l.startswith('---'): close(); i += 1; continue
    if l.startswith('|'):
        close(); rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        hdr = rows[0]; body = [r for r in rows[1:] if not all(set(c) <= set('-: ') for c in r)]
        outl.append('<table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in hdr) + '</tr></thead><tbody>' +
                    ''.join('<tr>' + ''.join(('<td class="st">%s</td>' if (j == 1 and len(c) < 26) else '<td>%s</td>') % inline(c) for j, c in enumerate(r)) + '</tr>' for r in body) + '</tbody></table>')
        continue
    m = re.match(r'^(\d+)\. (.*)', l)
    if m:
        if inlist != 'ol': close(); outl.append('<ol>'); inlist = 'ol'
        item = m.group(2); i += 1
        while i < len(lines) and lines[i].startswith('   ') and lines[i].strip(): item += ' ' + lines[i].strip(); i += 1
        outl.append('<li>%s</li>' % inline(item)); continue
    if not l.strip(): close(); i += 1; continue
    close(); para = l; i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '---')) and not re.match(r'^\d+\. ', lines[i]):
        para += ' ' + lines[i].strip(); i += 1
    outl.append('<p>%s</p>' % inline(para))
close()
body = '\n'.join(outl)
page = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>The recorded herd: what would be needed</title>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="icon-192.png">
<style>
:root{--paper:#F6F3EB;--ink:#1C1B18;--ink-2:#4A4842;--hair:#C9C4B5;--spot:#8E4A1C;--green:#1F4D3F}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Georgia,"Times New Roman",serif;font-size:16px;line-height:1.5}
.page{max-width:760px;margin:0 auto;padding:24px 20px 60px}
.runhead{display:flex;justify-content:space-between;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:var(--ink-2);border-bottom:1px solid var(--ink);padding:0 0 8px;margin:0 0 28px}
.runhead a{color:var(--ink-2);text-decoration:none}
h1{font-weight:normal;font-size:28px;line-height:1.2;margin:0 0 14px}
h2{font-weight:normal;font-size:19px;margin:30px 0 8px;border-top:1px solid var(--hair);padding-top:14px}
p{margin:0 0 .8em;text-align:justify;hyphens:auto}
table{border-collapse:collapse;width:100%;font-family:Arial,Helvetica,sans-serif;font-size:12.5px;line-height:1.4;margin:8px 0 14px}
th{text-align:left;font-weight:bold;padding:6px 8px 6px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);vertical-align:bottom}
td{padding:6px 8px 6px 0;border-bottom:1px solid var(--hair);vertical-align:top}
td.st{white-space:nowrap;color:var(--spot);text-align:center;padding:6px 12px}
th.st{text-align:center;padding:6px 12px}
ol{padding-left:1.4em}li{margin:0 0 .5em}
.dl{font-family:Arial,Helvetica,sans-serif;font-size:13px;margin:0 0 20px}
.dl a{color:var(--green)}
@media print{.dl{display:none}body{background:#fff}.page{max-width:none;padding:0}}
</style></head><body><div class="page">
<div class="runhead"><span><a href="/cattle-demo/">Ng'ombe, the demo</a> · Zamai Solutions</span><span>Spec sheet v0 · 6 November 2026</span></div>
<p class="dl"><a href="spec-sheet.pdf">Download as PDF</a></p>
''' + body + '''
</div></body></html>'''
page = page.replace("<th>Status</th>", "<th class=\"st\">Status</th>")
open(out, 'w', encoding='utf-8').write(page)
print('spec page written', len(page))

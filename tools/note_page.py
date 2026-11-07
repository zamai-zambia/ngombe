# Build the printable concept note (HTML for print.mjs) from internal/cattle/note/CONCEPT_NOTE.md.
#   python note_page.py <md> <out.html> <shots_dir> <qr.png>
# Markers in the markdown: [QR] places the QR code with the address; [SHOTS: id|caption|id|caption] places up to two
# phone screens side by side with captions. Images are embedded as data URIs so the HTML prints from anywhere.
import re, sys, html, base64, os
src, out, shots, qr = sys.argv[1:5]
md = open(src, encoding='utf-8').read()
def data_uri(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(https?://[^\s)]+)", r'<a href="\1">\1</a>', t)
    return t
lines = md.split('\n'); outl = []; i = 0; inlist = None
def close():
    global inlist
    if inlist: outl.append('</%s>' % inlist); inlist = None
while i < len(lines):
    l = lines[i]
    if l.startswith('# '): close(); outl.append('<h1>%s</h1>' % inline(l[2:])); i += 1; continue
    if l.startswith('## '):
        close(); cls = ''
        outl.append('<h2%s>%s</h2>' % (cls, inline(l[3:]))); i += 1; continue
    if l.strip() == '[PAGE]':
        close(); outl.append('<div class="np"></div>'); i += 1; continue
    if l.strip() == '[QR]':
        close(); outl.append('<div class="qr"><a href="https://ngombe.zamai.pro"><img src="%s" alt="QR code"></a><div><b><a href="https://ngombe.zamai.pro">ngombe.zamai.pro</a></b><br>On paper: scan to open the demo on a phone. On a phone: tap the address.<br>Chrome or Edge, then "Install on this phone".<br>Questions: Christoph Lindinger, <a href="tel:+260962653100">+260 96 2653100</a> · <a href="mailto:chris@zamai.pro">chris@zamai.pro</a></div></div>' % data_uri(qr)); i += 1; continue
    if l.strip() == '[QRC]':
        close(); outl.append('<div class="qr"><a href="https://ngombe.zamai.pro/contact.html"><img src="%s" alt="Contact QR code"></a><div><b>Christoph Lindinger</b> · Director, Yumi Milling Ltd · Zamai Solutions<br><a href="tel:+260962653100">+260 96 2653100</a> · <a href="mailto:chris@zamai.pro">chris@zamai.pro</a> · <a href="https://wa.me/260776621255">WhatsApp, the Zamai line +260 776 621 255</a><br>On paper: scan to save the contact. On a phone: <a href="https://ngombe.zamai.pro/contact.html">tap here to add the contact</a>.</div></div>' % data_uri(os.path.join(os.path.dirname(qr), 'qr_contact.png'))); i += 1; continue
    m = re.match(r'^\[SHOTS: (.*)\]$', l.strip())
    if m:
        close(); parts = [p.strip() for p in m.group(1).split('|')]
        cells = []
        for k in range(0, len(parts) - 1, 2):
            p = os.path.join(shots, parts[k] + '.png')
            cells.append('<figure><img src="%s" alt=""><figcaption>%s</figcaption></figure>' % (data_uri(p), inline(parts[k + 1])))
        prev_shots = bool(outl) and outl[-1].startswith('<div class="shots')
        outl.append('<div class="shots%s">' % (' np' if prev_shots else '') + ''.join(cells) + '</div>'); i += 1; continue
    if l.startswith('|'):
        close(); rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        hdr = rows[0]; body = [r for r in rows[1:] if not all(set(c) <= set('-: ') for c in r)]
        outl.append('<table><thead><tr>' + ''.join('<th>%s</th>' % inline(c) for c in hdr) + '</tr></thead><tbody>' +
                    ''.join('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>' for r in body) + '</tbody></table>')
        continue
    m = re.match(r'^(\d+)\. (.*)', l)
    if m:
        if inlist != 'ol': close(); outl.append('<ol>'); inlist = 'ol'
        item = m.group(2); i += 1
        while i < len(lines) and lines[i].startswith('   ') and lines[i].strip(): item += ' ' + lines[i].strip(); i += 1
        outl.append('<li>%s</li>' % inline(item)); continue
    if l.startswith('- '):
        if inlist != 'ul': close(); outl.append('<ul>'); inlist = 'ul'
        item = l[2:]; i += 1
        while i < len(lines) and lines[i].startswith('  ') and lines[i].strip() and not lines[i].startswith('- '): item += ' ' + lines[i].strip(); i += 1
        outl.append('<li>%s</li>' % inline(item)); continue
    if not l.strip(): close(); i += 1; continue
    close(); para = l; i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '- ', '[')) and not re.match(r'^\d+\. ', lines[i]):
        para += ' ' + lines[i].strip(); i += 1
    cls = ' class="lead"' if re.fullmatch(r'\*\*[^*]+\*\*', para.strip()) else ''
    outl.append('<p%s>%s</p>' % (cls, inline(para)))
close()
body = '\n'.join(outl)
page = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ng'ombe: a recorded herd. Concept note</title>
<meta name="robots" content="noindex">
<style>
:root{--paper:#fff;--ink:#1C1B18;--ink-2:#4A4842;--hair:#C9C4B5;--spot:#8E4A1C;--green:#1F4D3F}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Georgia,"Times New Roman",serif;font-size:10.6pt;line-height:1.42}
.page{max-width:760px;margin:0 auto;padding:10px 0 40px}
h1{font-weight:normal;font-size:22pt;line-height:1.15;margin:0 0 2px}
h1+h2{border:0;margin:0 0 10px;padding:0;font-size:14pt;color:var(--ink-2);line-height:1.3}
h2{font-weight:normal;font-size:15pt;margin:22pt 0 6pt;border-top:1px solid var(--hair);padding-top:10pt;page-break-after:avoid}
p{margin:0 0 .65em;text-align:left}
p.lead{page-break-after:avoid;margin-bottom:.3em}
table{border-collapse:collapse;width:100%;font-family:Arial,Helvetica,sans-serif;font-size:9.5pt;line-height:1.35;margin:6pt 0 12pt;page-break-inside:avoid}
th{text-align:left;font-weight:bold;padding:4pt 8pt 4pt 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);vertical-align:bottom}
td{padding:4pt 8pt 4pt 0;border-bottom:1px solid var(--hair);vertical-align:top}
ol,ul{padding-left:1.3em;margin:0 0 .8em}li{margin:0 0 .35em}
a{color:var(--green);text-decoration:none}
.qr{display:flex;gap:14px;align-items:center;border:1px solid var(--hair);padding:8px 12px;margin:4pt 0 10pt;font-family:Arial,Helvetica,sans-serif;font-size:9.5pt;page-break-inside:avoid}
.qr img{width:70px;height:70px}
.shots{display:flex;gap:14px;align-items:flex-start;margin:8pt 0 12pt;page-break-inside:avoid}
figure{margin:0;flex:1}
figure img{width:100%;max-height:135mm;object-fit:contain;object-position:top;border:1px solid var(--hair);border-radius:10px;display:block}
.np{page-break-before:always}
h2.np{border-top:0;padding-top:0;margin-top:0}
.shots figure{max-width:47%}
.shots{justify-content:center}
figcaption{font-family:Arial,Helvetica,sans-serif;font-size:8.5pt;color:var(--ink-2);margin-top:3pt;line-height:1.3}
@page{size:A4}
</style></head><body><div class="page">
''' + body + '''
</div></body></html>'''
open(out, 'w', encoding='utf-8').write(page)
print('note page written', len(page))

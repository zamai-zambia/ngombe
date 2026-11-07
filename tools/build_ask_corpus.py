# Build netlify/functions/ngombe_ask_data/corpus.mjs: what the "Ask about Ng'ombe" agent answers from.
#   python tools/cattle-demo/build_ask_corpus.py
# Sources: the concept note (outward text), the spec sheet (outward edits as spec_page.py makes them), and the beef
# markets research note. Internal file names and the translator's name are removed. Rebuild on every change.
import re, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
note = rd('internal/cattle/note/CONCEPT_NOTE.md')
note = re.sub(r'\n\[QR\]\n|\n\[QRC\]\n', '\n', note)
note = re.sub(r'\[SHOTS: [^\]]*\]', '(screens of the demo are shown here in the printed note)', note)
spec = rd('internal/cattle/CATTLE_SPEC_SHEET.md')
spec = spec.replace("Companion to the demo at zamai.pro/cattle-demo/ and to\n`CATTLE_APP_SPEC.md` (the product spec) and `CATTLE_PROGRAMME_CONCEPT.md` (the programme).", "Companion to the demo at ngombe.zamai.pro.")
spec = spec.replace("Matthew Sakala is translating the demo's 300 lines now.", "Matthew Sakala is translating the demo's lines now.")
spec = re.sub(r'`[A-Z_]+\.md`', 'an internal document', spec)
research = rd('internal/cattle/BEEF_MARKETS_AND_GRADING_2026-11-07.md')
# the research note is internal: keep it, but drop the Zambeef ownership section, which carries an unverified claim
research = re.sub(r'\n## 7\. Zambeef.*?(?=\n## Sources)', '\n## 7. (omitted)\n', research, flags=re.S)
for nm in ['Musunga', 'Maxwell', 'Khama', 'Enock']:
    spec = spec.replace(nm, 'a Tonga speaker'); note = note.replace(nm, 'a Tonga speaker')
corpus = ("# DOCUMENT 1: the concept note (version 0.2, 7 November 2026)\n\n" + note +
          "\n\n# DOCUMENT 2: the spec sheet (what would be needed)\n\n" + spec +
          "\n\n# DOCUMENT 3: beef markets, grading and what records add per animal (research note, 7 November 2026; 93 sources)\n\n" + research)
out = os.path.join(ROOT, 'netlify/functions/ngombe_ask_data/corpus.mjs')
open(out, 'w', encoding='utf-8').write('export default ' + json.dumps(corpus, ensure_ascii=False) + ';\n')
print('corpus', len(corpus), 'chars ->', out)

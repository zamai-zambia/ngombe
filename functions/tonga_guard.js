// Triage for zamai.pro/tonga (24 Oct 2026; Chris: "the wider it's shared, the more nonsense and naughty input we'll
// get"). Pure functions, no I/O; netlify/functions/tonga.js applies them. Nothing here rejects real Tonga: a flag
// sends a contribution to QUARANTINE (a human still reads it, after the clean queue), it never deletes it.
//
// English word list: "List of Dirty, Naughty, Obscene, and Otherwise Bad Words", LDNOOBW, English file `en`
// (https://github.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words, commit 5faf2ba, CC BY 4.0),
// copied verbatim to ldnoobw_en.json. It covers profanity, sexual terms and slurs. We take some entries OUT
// (SCHOOL_OK below) because the translator is for everyday and school language, and school language includes
// reproductive health and safeguarding: a child must be able to translate "rape", a health booklet "penis", a farmer
// "the cock crows" or "how to kill weeds".
// There is NO Tonga word list: we never compose Tonga. If Chris wants one, a speaker supplies it (not Fr Musunga).
//
// Lexicon: the Tonga word forms attested 3+ times in our real Tonga corpus (internal attest_real.json, 74,980 forms),
// used ONLY as a signal (the share of words found), never to reject: dialect and new spellings are data.
const BAD = require('./ldnoobw_en.json');
const LEX = new Set(require('./tonga_lexicon.json'));

const SCHOOL_OK = new Set(['anus', 'clitoris', 'ejaculation', 'genitals', 'intercourse', 'nipple', 'nipples', 'penis',
  'rectum', 'semen', 'sex', 'sexual', 'sexually', 'sexuality', 'vagina', 'vulva', 'rape', 'raping', 'rapist',
  'date rape', 'daterape', 'incest', 'suck', 'sucks', 'cock', 'cocks', 'snatch', 'escort', 'domination', 'eunuch',
  'how to kill', 'ball kicking', 'hard core', 'hardcore', 'undressing', 'tied up', 'grope', 'bondage', 'butt']);
// measured 24 Oct on the 221,575 stage 9 training pairs: Tonga side 0 hits; English side 137, of which 'bondage' (42,
// the Bible's 'out of bondage') and 'butt' (93) are school and story language, so they are in SCHOOL_OK too
const WORDS = new Set(), PHRASES = [];
for (const w of BAD) {
  const x = w.toLowerCase().trim();
  if (!x || SCHOOL_OK.has(x)) continue;
  if (/\s/.test(x)) PHRASES.push(' ' + x + ' ');
  else WORDS.add(x);
}

const LEET = { '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's', '!': 'i' };
function norms(text) {
  const t = String(text || '').toLowerCase().normalize('NFKC');
  const plain = t.replace(/[^\p{L}🖕&]+/gu, ' ').replace(/(\p{L})\1{2,}/gu, '$1');
  const leet = t.replace(/[013457@$!]/g, (c) => LEET[c]).replace(/[^\p{L}🖕&]+/gu, ' ').replace(/(\p{L})\1{2,}/gu, '$1');
  // letters spread out with dots or spaces ("f u c k", "s.h.i.t")
  const joined = t.replace(/\b(\p{L})(?:[\s.\-_*]+(\p{L})\b)+/gu, (m) => m.replace(/[\s.\-_*]+/g, ''));
  return [plain, leet, joined.replace(/[^\p{L}]+/gu, ' ')].map((s) => ' ' + s.replace(/\s+/g, ' ').trim() + ' ');
}
// [matched entries]; empty = clean
function profanity(text) {
  const hit = new Set();
  for (const n of norms(text)) {
    for (const w of n.trim().split(' ')) if (WORDS.has(w)) hit.add(w);
    for (const p of PHRASES) if (n.includes(p)) hit.add(p.trim());
    if (n.includes('🖕')) hit.add('🖕');
  }
  return [...hit];
}

// stricter, for nicknames only (they are short and run words together: "BigDick69"): any listed word of 4+ letters, or
// a listed 3-letter word at the start or end, inside the letters with everything else removed
const LOOSE = [...WORDS].filter((w) => /^\p{L}+$/u.test(w) && w.length >= 4);
const LOOSE3 = [...WORDS].filter((w) => /^\p{L}{3}$/u.test(w));
function profanityLoose(text) {
  const hit = new Set(profanity(text));
  for (const n of norms(text)) {
    const flat = n.replace(/[^\p{L}]/gu, '');
    for (const w of LOOSE) if (flat.includes(w)) hit.add(w);
    for (const w of LOOSE3) if (flat.startsWith(w) || flat.endsWith(w)) hit.add(w);
  }
  return [...hit];
}

// personal data: links, e-mail addresses, phone numbers -> replaced, and the kinds found
const RX_EMAIL = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g;
const RX_URL = /\b(?:https?:\/\/|www\.)\S+|\b(?:wa\.me|t\.me|bit\.ly|tinyurl\.com|chat\.whatsapp\.com)\/\S*|\b[\w-]{2,}\.(?:com|net|org|zm|co|io|ly|me|info|biz|xyz|app|link|tk|ru|cn|site|online|shop|top|club|live|vip|ke|za|zw|uk|us)\b(?:\/\S*)?/gi;
const RX_PHONE = /(?:\+|\b)\d[\d\s().-]{7,}\d\b/g;
function stripPersonal(text) {
  const kinds = new Set();
  let s = String(text || '');
  s = s.replace(RX_EMAIL, () => { kinds.add('email'); return '[email]'; });
  s = s.replace(RX_URL, () => { kinds.add('link'); return '[link]'; });
  s = s.replace(RX_PHONE, (m) => ((m.match(/\d/g) || []).length >= 9 ? (kinds.add('phone'), '[phone]') : m));
  return { text: s, kinds: [...kinds] };
}

// gibberish by character patterns only (never by the lexicon): [reasons]
const KEYBOARD = /(?:qwert|werty|asdf|sdfg|dfgh|fghj|ghjk|hjkl|zxcv|xcvb|cvbn|vbnm|yxcv|qwer|uiop|poiu|lkjh|mnbv)/i;
function gibberish(text) {
  const t = String(text || '');
  const why = [];
  const letters = (t.match(/\p{L}/gu) || []).length, nonspace = t.replace(/\s/g, '').length;
  if (nonspace >= 4 && letters / nonspace < 0.5) why.push('mostly symbols or digits');
  if (/(\p{L})\1{3,}/u.test(t)) why.push('one letter repeated');
  if (KEYBOARD.test(t)) why.push('keyboard run');
  const toks = t.toLowerCase().match(/\p{L}+/gu) || [];
  if (toks.some((w) => w.length > 30)) why.push('very long word');
  const long = toks.filter((w) => w.length >= 4);
  if (long.length >= 2 && long.filter((w) => !/[aeiouy]/.test(w)).length / long.length > 0.5) why.push('words without vowels');
  for (let i = 0; i + 3 < toks.length; i++) {
    if (toks[i] === toks[i + 1] && toks[i] === toks[i + 2] && toks[i] === toks[i + 3]) { why.push('same word 4 times'); break; }
  }
  return why;
}
// share of words (2+ letters) found in the attested Tonga lexicon: null when there are no such words
function lexShare(text) {
  const toks = (String(text || '').toLowerCase().match(/\p{L}{2,}/gu) || []);
  if (!toks.length) return null;
  return Math.round(100 * toks.filter((w) => LEX.has(w)).length / toks.length) / 100;
}

module.exports = { profanity, profanityLoose, stripPersonal, gibberish, lexShare, SCHOOL_OK };

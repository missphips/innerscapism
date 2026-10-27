"""Assemble innerscapism.com from the English source pages.

Run from anywhere:  python3 _build/build_site.py
- adds the shared menu and footer to every English page
- sets canonical / language-alternate tags and clean links (/work, /about ...)
- builds the European Portuguese pages in pt/ from translations.py
- reports any English text that still has no translation
"""
import html, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, '_build'))
from translations import T, KEEP, PAGE_T  # noqa: E402

SITE = 'https://innerscapism.com'
PAGES = [  # file, clean path, menu item marked as current
    ('index.html', '/', 'home'),
    ('work.html', '/work', 'work'),
    ('innerware.html', '/innerware', 'work'),
    ('about.html', '/about', 'about'),
    ('contact.html', '/contact', 'contact'),
]
FILE_FOR = {'/': 'index.html', '/work': 'work.html', '/innerware': 'innerware.html',
            '/about': 'about.html', '/contact': 'contact.html'}

NAV_STYLE = ('display:flex; align-items:center; justify-content:space-between; padding: 28px 64px; '
             'position: sticky; top:0; z-index: 10; background: oklch(97% 0.01 70 / 0.9); backdrop-filter: blur(6px);')
LOGO_STYLE = ("font-family:'Fraunces', serif; font-size: 26px; letter-spacing: 0.02em; font-weight: 500; "
              "text-decoration:none; color: oklch(25% 0.02 40);")
PILL_STYLE = ('text-decoration:none; padding: 10px 22px; background: #a3453d; color: oklch(98% 0.01 70); '
              'border-radius: 999px;')


def nav(current):
    def cur(key):
        return ' aria-current="page"' if key == current else ''
    return f'''<!-- NAV -->
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="nav" style="{NAV_STYLE}">
    <a href="/" style="{LOGO_STYLE}" aria-label="innerscapism, home">innerscapism</a>
    <nav class="nav-links" aria-label="Main menu" style="display:flex; gap: 36px; align-items:center; font-size: 15px;">
      <!--SWITCH-->
      <a href="/#experiences" style="text-decoration:none;">Experiences</a>
      <a href="/work" style="text-decoration:none;"{cur('work')}>Work &amp; Systems</a>
      <a href="/about" style="text-decoration:none;"{cur('about')}>About</a>
      <a href="/contact" class="cta-pill" style="{PILL_STYLE}"{cur('contact')}>Contact</a>
    </nav>
  </div>
  <!-- /NAV -->'''


FOOTER = '''<!-- FOOTER -->
  <footer class="footer" style="padding: 40px 64px; border-top: 1px solid oklch(88% 0.015 60); display:flex; justify-content:space-between; align-items:center; gap: 24px; font-size: 14px; color: oklch(50% 0.02 40);">
    <a href="/" style="font-family:'Fraunces', serif; font-size: 17px; color: oklch(30% 0.02 40); text-decoration: none;">innerscapism</a>
    <nav class="footer-links" aria-label="Footer">
      <a href="https://www.instagram.com/innerscapism/">Instagram</a>
    </nav>
  </footer>
  <!-- /FOOTER -->'''


# ---------------------------------------------------------------- helpers
def norm(t):
    return ' '.join(html.unescape(t).split())


def put_block(s, name, block):
    s = re.sub(rf'<!-- {name} -->.*?<!-- /{name} -->', f'<!-- {name} -->', s, flags=re.S)
    assert s.count(f'<!-- {name} -->') == 1, name
    return s.replace(f'<!-- {name} -->', block)


def clean_links(s, lang):
    """Site links stay clean on the live site; data-local makes them work from local files."""
    def fix(m):
        path, frag = m.group(1), m.group(2) or ''
        base = path.rstrip('/') or '/'
        if base.startswith('/pt'):
            base = base[3:] or '/'
        if base not in FILE_FOR:
            return m.group(0)
        live = ('/pt' + (base if base != '/' else '/')) if lang == 'pt' else base
        return f'href="{live}{frag}" data-local="{FILE_FOR[base]}{frag}"'
    s = re.sub(r'\sdata-local="[^"]*"', '', s)
    return re.sub(r'href="(/(?!/)[^"#]*)(#[^"]*)?"', fix, s)


def head_tags(s, lang, path):
    en_url = SITE + path
    pt_url = SITE + '/pt' + (path if path != '/' else '/')
    me = pt_url if lang == 'pt' else en_url
    s = re.sub(r'<html lang="[^"]*">', '<html lang="pt-PT">' if lang == 'pt' else '<html lang="en">', s, count=1)
    s = re.sub(r'\n<link rel="alternate" hreflang="[^"]*" href="[^"]*">', '', s)
    s = re.sub(r'\n<meta property="og:locale(?::alternate)?" content="[^"]*">', '', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{me}">', s, count=1)
    alts = (f'<link rel="canonical" href="{me}">'
            f'\n<link rel="alternate" hreflang="en" href="{en_url}">'
            f'\n<link rel="alternate" hreflang="pt-PT" href="{pt_url}">'
            f'\n<link rel="alternate" hreflang="x-default" href="{en_url}">'
            f'\n<meta property="og:locale" content="{"pt_PT" if lang == "pt" else "en_GB"}">'
            f'\n<meta property="og:locale:alternate" content="{"en_GB" if lang == "pt" else "pt_PT"}">')
    s, n = re.subn(r'<link rel="canonical" href="[^"]*">', alts, s, count=1)
    assert n == 1
    return s


def switch(lang, fname, path):
    if lang == 'en':
        return (f'<span class="lang-switch"><span aria-current="true">EN</span> · '
                f'<a href="/pt{path if path != "/" else "/"}" data-local="pt/{fname}" hreflang="pt-PT" lang="pt-PT" '
                f'aria-label="Ver em português">PT</a></span>')
    return (f'<span class="lang-switch"><a href="{path}" data-local="../{fname}" hreflang="en" lang="en" '
            f'aria-label="View in English">EN</a> · <span aria-current="true">PT</span></span>')


def place_switch(s, lang, fname, path):
    s = re.sub(r'<span class="lang-switch">[^\n]*?</span></span>|<span class="lang-switch">.*?PT</a></span>',
               '<!--SWITCH-->', s)
    assert s.count('<!--SWITCH-->') == 1, fname
    return s.replace('<!--SWITCH-->', switch(lang, fname, path))


def fix_dims(s, base_dir):
    def one(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        f = os.path.normpath(os.path.join(base_dir, src))
        if not os.path.exists(f):
            print('  MISSING image', src)
            return tag
        out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', f], capture_output=True, text=True).stdout
        w = re.search(r'pixelWidth: (\d+)', out).group(1)
        h = re.search(r'pixelHeight: (\d+)', out).group(1)
        tag = re.sub(r'\s(width|height)="\d+"', '', tag)
        return tag.replace('<img ', f'<img width="{w}" height="{h}" ', 1)
    return re.sub(r'<img [^>]*>', one, s)



def asset_versions(s):
    """Add ?v=<content hash> to the shared CSS/JS so browsers never keep a stale copy."""
    import hashlib
    for rel in ('assets/css/innerscapism.css', 'assets/js/reveal.js'):
        if os.path.exists(rel):
            v = hashlib.md5(open(rel, 'rb').read()).hexdigest()[:8]
            s = re.sub(r'(["/])' + re.escape(rel) + r'(\?v=[0-9a-f]+)?"', r'\g<1>' + rel + '?v=' + v + '"', s)
    return s

# ---------------------------------------------------------------- translation
used = set()
page_t = {}  # per-page overrides, set while translating each page


def lookup(key):
    if key in page_t:
        return page_t[key]
    if key in T:
        used.add(key)
        return T[key]
    return None


def tr_text(raw):
    key = norm(raw)
    val = lookup(key) if key else None
    if val is None:
        return raw
    lead = raw[:len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    return lead + html.escape(val, quote=False).replace(' ', '&nbsp;') + trail


def tr_attr(m):
    val = lookup(norm(m.group(2)))
    if val is None:
        return m.group(0)
    return f'{m.group(1)}="{html.escape(val, quote=True)}"'


def translate(s):
    parts = re.split(r'(<style.*?</style>|<script.*?</script>|<svg.*?</svg>|<[^>]+>)', s, flags=re.S)
    out = []
    for part in parts:
        if part.startswith(('<style', '<script', '<svg')):
            out.append(part)
        elif part.startswith('<'):
            out.append(re.sub(r'\b(content|alt|aria-label)="([^"]*)"', tr_attr, part))
        else:
            out.append(tr_text(part))
    return ''.join(out)


def untranslated(s):
    body = re.sub(r'<style.*?</style>|<script.*?</script>|<svg.*?</svg>', '', s, flags=re.S)
    found = set()
    for t in re.split(r'<[^>]+>', body):
        k = norm(t)
        if k and k not in KEEP and not k.startswith('“') and re.search(r'[A-Za-z]', k):
            found.add(k)
    for m in re.finditer(r'\b(?:content|alt|aria-label)="([^"]*)"', s):
        k = norm(m.group(1))
        if k and k not in KEEP and not k.startswith(('http', 'width=')) and re.search(r'[A-Za-z]{3}', k):
            found.add(k)
    return found


# ---------------------------------------------------------------- build
os.makedirs('pt', exist_ok=True)
problems = 0
for fname, path, current in PAGES:
    en = open(fname).read()
    en = put_block(en, 'NAV', nav(current))
    en = put_block(en, 'FOOTER', FOOTER)
    en = head_tags(en, 'en', path)
    en = clean_links(en, 'en')
    en = place_switch(en, 'en', fname, path)
    en = fix_dims(en, '.')
    en = asset_versions(en)
    open(fname, 'w').write(en)

    english_text = untranslated(en)
    page_t.clear()
    page_t.update(PAGE_T.get(fname, {}))
    pt = translate(en)
    pt = re.sub(r'(src|href)="(assets/[^"]*)"', r'\1="../\2"', pt)
    pt = head_tags(pt, 'pt', path)
    pt = clean_links(pt, 'pt')
    pt = place_switch(pt, 'pt', fname, path)
    open('pt/' + fname, 'w').write(pt)

    left = sorted(english_text & untranslated(pt))
    if left:
        problems += len(left)
        print(f'{fname}: {len(left)} untranslated')
        for t in left:
            print('   ', repr(t))
    else:
        print(f'{fname}: ok')

print('unused translations:', len(set(T) - used))
sys.exit(1 if problems else 0)

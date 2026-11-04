"""プロフィールサイトを販売特設サイトのデザインで生成する。
usage: python3 _build/build.py
  入力: _build/source/{ja,en,zh}.html  … 旧サイト（文言の正本。写真は img/pNN.jpg 参照に置換済み）
        _build/base.css                … 販売サイトテンプレ（property-site/template）由来のCSS
  出力: index.html / en.html / zh.html （このあと lightbox.py で写真の拡大表示を付ける）
文言を直すときは source を直してから再生成する。
"""
import os, re, subprocess
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, '_build')
LIGHTBOX = '/Users/leetenki/AI_share/.claude/skills/property-site/scripts/lightbox.py'

SITE = 'https://leetenki.github.io/leetenki_profile/'  # リンクのサムネ（OGP）用の絶対URL
LANGS = {
    'ja': dict(out='index.html', html='ja', pdf='李天琦_紹介資料.pdf',
               font='"Noto Sans JP","Hiragino Sans","Yu Gothic",sans-serif',
               gf='Noto+Sans+JP'),
    'en': dict(out='en.html', html='en', pdf='profile_en.pdf',
               font='"Noto Sans JP","Helvetica Neue","Segoe UI",Arial,sans-serif',
               gf='Noto+Sans+JP'),
    'zh': dict(out='zh.html', html='zh-CN', pdf='profile_zh.pdf',
               font='"Noto Sans SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif',
               gf='Noto+Sans+SC'),
}
# 実績カードに添える動画（カードの日付・見出しは source の順番で特定）
# clip: 'nasdaq' = NASDAQ スクリーン放送の動画をカードの前に全幅で入れる
CARD_VIDEO = {}  # 2023年NASDAQは CARD_MOVIE に移した（以前は {5: 'nasdaq'}）
# ABEMA・TBS の数秒クリップ（ユーザーが秒数を決めたら video/ に置き、ここに足す）
# 例: CARD_CLIP = {3: 'abema2020', 6: 'tbs', 8: 'abema2023'}
CARD_CLIP = {}
# 写真の代わりに横幅いっぱいの動画を置くカード（番号は実績カードの並び順・0始まり。カードを足したらずらす）: (PC用の動画, スマホ用の動画, クリック先)。スマホ用は縦横比4:3なら寄せた版
CARD_MOVIE = {1: ('dena_techcon_w', 'dena_techcon2', 'https://youtu.be/5OuwwV_RwPU?t=1083'),
              4: ('abema2020', 'abema2020', 'https://youtu.be/PrlyDQ1_6Us?t=144'),
              6: ('nasdaq_fix_land', 'nasdaq_fix_port', 'https://youtu.be/hfWxPv_i40o?t=83', '916'),  # 確定版（2026-11-05 fix）。heroとは別ファイルなのでheroを替えても変わらない
              7: ('tbs2023', 'tbs2023', 'https://youtu.be/5dfu0bnIThw'),  # クリック先は出典のVTR
              9: ('abema2023', 'abema2023', 'https://youtu.be/IACYugVFkCc?t=137'),
              10: ('rakumachi2025', 'rakumachi2025', 'https://youtu.be/D5KXi3YbLIs')}
# 4つ目はスマホ用の縦横比（省略時: スマホ用が別ファイルなら 43=4:3）
YT_LABEL = {'ja': 'YouTubeで見る', 'en': 'Watch on YouTube', 'zh': '在YouTube观看'}

SEP = re.compile(r'\s*[─—]\s*')


def esc_inner(tag):
    return ''.join(str(c) for c in tag.contents).strip()


def parse(lang):
    s = BeautifulSoup(open(os.path.join(B, 'source', lang + '.html'), encoding='utf-8'), 'html.parser')
    d = {}
    d['title'] = s.title.text
    nav = s.select_one('nav.lang')
    d['print'] = nav.select_one('button').text.replace('🖨', '').strip()
    h = s.select_one('header.hero')
    d['label'] = h.select_one('.hero-label').text.strip()
    nm = h.select_one('.hero-name')
    d['name_small'] = nm.small.text.strip()
    nm.small.extract()
    d['name'] = nm.text.strip()
    d['role'] = h.select_one('.hero-title').text.strip()
    d['sub'] = h.select_one('.hero-sub').text.strip()
    d['photo'] = h.select_one('.hero-photo img')
    d['stats'] = [(x.select_one('.num').text.strip(), x.select_one('.label').text.strip()) for x in h.select('.stat')]
    secs = s.select('.content > section')
    def h2(sec):
        t = sec.h2
        en = t.span.text.strip() if t.span else ''
        if t.span:
            t.span.extract()
        return t.text.strip(), en
    d['sum_h'], _ = h2(secs[0])
    d['sum_p'] = [esc_inner(p) for p in secs[0].select('p')]
    d['tl_h'], _ = h2(secs[1])
    d['tl'] = [(tr.select_one('.d').text.strip(), esc_inner(tr.select_one('.b')), 'hl' in (tr.get('class') or []))
               for tr in secs[1].select('tr')]
    d['hi_h'], _ = h2(secs[2])
    cards = []
    for a in secs[2].select('article.card'):
        c = {}
        c['date'] = a.select_one('.date').text.strip()
        c['title'] = esc_inner(a.select_one('h3'))
        body = a.select_one('.card-body > div')
        c['ps'] = [esc_inner(p) for p in body.select('p') if 'src' not in (p.get('class') or [])]
        c['src'] = [esc_inner(p) for p in body.select('p.src')]
        im = a.select_one('.imgs')
        c['imgs'] = [(i['src'], i.get('alt', '')) for i in im.select('img')]
        c['cap'] = esc_inner(im.select_one('.cap')) if im.select_one('.cap') else ''
        cards.append(c)
    d['cards'] = cards
    d['media_h'], _ = h2(secs[3])
    rows = secs[3].select('tr')
    d['media_th'] = [th.text.strip() for th in rows[0].select('th')]
    d['media'] = [[esc_inner(td) for td in r.select('td')] for r in rows[1:]]
    d['foot'] = s.select_one('footer').text.strip()
    return d


def img_size(src):
    out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', os.path.join(ROOT, src)],
                         capture_output=True, text=True).stdout
    w = int(re.search(r'pixelWidth: (\d+)', out).group(1)); h = int(re.search(r'pixelHeight: (\d+)', out).group(1))
    return w, h


def fig(src, alt, cap='', cls=''):
    w, h = img_size(src)
    c = f'<figcaption><span class="t">{cap}</span></figcaption>' if cap else ''
    return f'<figure class="rv zoom {cls}"><img src="{src}" width="{w}" height="{h}" loading="lazy" alt="{alt}">{c}</figure>'


def split_title(t):
    p = SEP.split(t, maxsplit=1)
    return (p[0], p[1]) if len(p) == 2 else (t, '')


def lazy_video(base, cls='', poster=True):
    p = f' poster="{base}.poster.jpg"' if poster else ''
    return (f'<video class="lazy {cls}" muted loop playsinline webkit-playsinline x5-playsinline '
            f'x5-video-player-type="h5-page" preload="none"{p} data-webm="{base}.webm" data-mp4="{base}.mp4"></video>')


def render(lang):
    L = LANGS[lang]; d = parse(lang)
    css = open(os.path.join(B, 'base.css'), encoding='utf-8').read().replace('__FONT__', L['font'])
    langs = ''.join(f'<a href="{LANGS[k]["out"] if k != "ja" else "./"}"{" class=on" if k == lang else ""}>{n}</a>'
                    for k, n in (('ja', 'JP'), ('en', 'EN'), ('zh', '中文')))
    first, *rest = d['label'].split('─')
    o = []
    o.append(f'''<!DOCTYPE html>
<html lang="{L['html']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{d['title']}</title>
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="{d['role']}">
<meta property="og:type" content="profile">
<meta property="og:title" content="{d['title']}">
<meta property="og:description" content="{d['role']}">
<meta property="og:url" content="{SITE}{'' if L['out'] == 'index.html' else L['out']}">
<meta property="og:image" content="{SITE}img/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}img/og.jpg">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 fill=%27%230b0d10%27/%3E%3Ctext x=%2716%27 y=%2722%27 font-size=%2716%27 text-anchor=%27middle%27 fill=%27%23c9a962%27 font-family=%27sans-serif%27%3ELT%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={L['gf']}:wght@200;300;400;500;700&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>

<div class="bar" id="bar">
  <div class="brand">{d['name']}<small>{d['name_small']}</small></div>
  <nav class="tools"><span class="lang">{langs}</span><a class="pdf" href="{L['pdf']}" target="_blank" rel="noopener">PDF</a></nav>
</div>

<header class="hero">
  <video id="heroVideo" muted loop playsinline webkit-playsinline x5-playsinline x5-video-player-type="h5-page" autoplay preload="auto" aria-hidden="true"></video>
  <img class="poster" id="heroPoster" src="video/hero5_land.poster.jpg" alt="" aria-hidden="true">
  <div class="in">
    <p class="en">{first.strip()}</p>
    <h1 class="nm">{d['name']}<small>{d['name_small']}</small></h1>
    <p class="role">{d['role']}</p>
    <ul class="spec">{''.join(f'<li>{n}</li>' for n, _ in d['stats'])}</ul>
  </div>
  <div class="scroll">SCROLL</div>
</header>

<div class="keys">
  <ul>{''.join(f'<li><div class="v">{n}</div><div class="k">{k}</div></li>' for n, k in d['stats'])}</ul>
</div>
''')
    # 01 summary
    o.append(f'''
<section class="light">
  <div class="wrap sum">
    <div class="rv">
      <div class="head"><p class="no">01 — Summary</p><h2>{d['sum_h']}</h2></div>
      <p class="lead2">{d['sub']}</p>
      {''.join(f'<p class="body">{p}</p>' for p in d['sum_p'])}
    </div>
    {fig(d['photo']['src'], d['photo'].get('alt', ''), cls='sum-ph')}
  </div>
</section>
''')
    # 02 timeline
    o.append(f'''
<section>
  <div class="wrap">
    <div class="head rv"><p class="no">02 — Career</p><h2>{d['tl_h']}</h2></div>
    <ol class="tline rv">{''.join(f'<li{" class=hl" if hl else ""}><span class="y">{y}</span><span class="t">{t}</span></li>' for y, t, hl in d['tl'])}</ol>
  </div>
</section>
''')
    # 03 highlights intro
    o.append(f'''
<section class="hi-intro light">
  <div class="wrap"><div class="head rv" style="margin:0"><p class="no">03 — Highlights</p><h2>{d['hi_h']}</h2></div></div>
</section>
''')
    for i, c in enumerate(d['cards']):
        t1, t2 = split_title(c['title'])
        dark = i % 2 == 0
        if CARD_VIDEO.get(i) == 'nasdaq':
            o.append(f'''
<section class="movie wide">
  {lazy_video('video/nasdaq_screen')}
  <div class="cap"><p class="no">{c['date']}</p><h2>{t1}</h2></div>
</section>
''')
        imgs = c['imgs']
        if len(imgs) == 1:
            g = fig(*imgs[0], cap=c['cap'])
        else:
            g = (f'<div class="grid grid-2">' + ''.join(fig(s, a) for s, a in imgs) + '</div>'
                 + (f'<p class="gcap">{c["cap"]}</p>' if c['cap'] else ''))
        clip = CARD_CLIP.get(i)
        if clip:
            g = f'<figure class="clip rv" data-nolb>{lazy_video("video/" + clip)}</figure>' + g
        srcs = ''.join(f'<p class="src">{x}</p>' for x in c['src'])
        head = f'''<div class="head"><p class="no">{c['date']}</p><h2>{t1}</h2>{f'<p class="sub">{t2}</p>' if t2 else ''}</div>'''
        body = ''.join(f'<p class="body">{p}</p>' for p in c['ps'])
        if CARD_MOVIE.get(i):
            pc, sp, url, *spar = CARD_MOVIE[i]
            spar = spar[0] if spar else ('43' if sp != pc else '')
            v = lazy_video('video/' + pc).replace('></video>', f' data-webm-sp="video/{sp}.webm" data-mp4-sp="video/{sp}.mp4"></video>', 1)
            cap = c['cap'] or (imgs[0][1] if imgs else '')
            o.append(f'''
<section class="card mvcard{'' if dark else ' light'}">
  <div class="wrap rv">{head}</div>
  <figure class="mvfull{' sp' + spar if spar else ''} rv" data-nolb><a href="{url}" target="_blank" rel="noopener">{v}</a></figure>
  <div class="wrap">
    <p class="mvcap">{cap}<a class="ytl" href="{url}" target="_blank" rel="noopener">{YT_LABEL[lang]} ↗</a></p>
    <div class="txt rv">{body}{srcs}</div>
  </div>
</section>
''')
            continue
        o.append(f'''
<section class="card{'' if dark else ' light'}">
  <div class="wrap cardw">
    <div class="txt rv">
      <div class="head"><p class="no">{c['date']}</p><h2>{t1}</h2>{f'<p class="sub">{t2}</p>' if t2 else ''}</div>
      {''.join(f'<p class="body">{p}</p>' for p in c['ps'])}
      {srcs}
    </div>
    <div class="ph">{g}</div>
  </div>
</section>
''')
    # 04 media
    th = d['media_th']
    o.append(f'''
<section class="paper2 light">
  <div class="wrap">
    <div class="head rv"><p class="no">04 — Media</p><h2>{d['media_h']}</h2></div>
    <div class="mtbl rv">{''.join(f'<div class="mr"><div class="md">{r[0]}</div><div class="mm">{r[1]}</div><div class="mc">{r[2]}</div></div>' for r in d['media'])}</div>
  </div>
</section>

<section class="movie walkup">
  <div class="walk-in">
    {lazy_video('video/nasdaq14_up')}
    <div class="cap"><p class="no">Profile</p><h2>{d['name']}</h2><p>{d['role']}</p>
      <ul class="spec">{''.join(f'<li>{n}</li>' for n, _ in d['stats'])}</ul>
      <p class="dl"><a href="{L['pdf']}" target="_blank" rel="noopener">PDF</a></p>
    </div>
  </div>
</section>

<footer><p>{d['foot']}</p></footer>
''')
    o.append(open(os.path.join(B, 'script.js'), encoding='utf-8').read())
    o.append('\n</body>\n</html>\n')
    path = os.path.join(ROOT, L['out'])
    html = ''.join(o)
    # YouTube へのリンクはすべて新しいタブで開く（出典・メディア一覧のリンクも含む）
    html = re.sub(r'<a href="(https://(?:youtu\.be|(?:www\.)?youtube\.com)/[^"]*)">', r'<a href="\1" target="_blank" rel="noopener">', html)
    open(path, 'w', encoding='utf-8').write(html)
    subprocess.run(['python3', LIGHTBOX, path], check=True, capture_output=True)
    print('wrote', L['out'], len(d['cards']), 'cards', len(d['tl']), 'timeline', len(d['media']), 'media')


if __name__ == '__main__':
    for k in LANGS:
        render(k)

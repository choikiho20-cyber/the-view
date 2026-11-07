"""The뷰 홈페이지 빌드 — site.config.json + templates/ + images/ → dist/

    python -X utf8 build.py

dist/ 에는 배포할 파일만 들어간다. 값은 전부 site.config.json, 구조는 templates/ (청풍파노라마뷰와 같은 뼈대, 값·색·사진만 다름).
빈 칸("")으로 남은 값은 끝에 [확인 필요] 목록으로만 나오고 손님 화면에는 안 보인다.
전화가 비어 있으면 전화·문자 자리에 예약 채널(에어비앤비 등) 링크가 나간다.
"""
import datetime
import hashlib
import json
import os
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

from PIL import Image

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
T = ROOT / "templates"
cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
todo_list = []
today = datetime.date.today()

name, phone, a = cfg["name"], cfg["phone"], cfg["address"]
tel = re.sub(r"[^0-9]", "", phone)
sms_tel = re.sub(r"[^0-9]", "", cfg["sms"] or phone)
domain = cfg["domain"].rstrip("/")
base = os.environ.get("BASE", "").rstrip("/") or domain or cfg["preview_url"].rstrip("/")  # BASE=http://localhost:8785/dist 로 로컬 확인
noindex = cfg["photos_temporary"] or not domain
addr = f"{a['region']} {a['city']} {a['street']}"
cap = cfg["capacity"]
g = cfg["geo"]
AI = set(cfg["ai_images"])
booking = [b for b in cfg.get("booking", []) if b["url"]]
book1 = booking[0] if booking else None

for k, label in (("domain", "도메인"), ("phone", "전화번호 (사장님 직통 — 지금은 예약 채널 링크로 대신)"), ("owner", "대표자 이름"), ("biz_no", "사업자등록번호"), ("ga4", "GA4 측정 ID"),
                 ("google_verify", "구글 서치콘솔 소유확인 값"), ("naver_verify", "네이버 서치어드바이저 소유확인 값")):
    if not cfg[k]:
        todo_list.append(label)
if not g["lat"]:
    todo_list.append("위도·경도 (네이버 지도 주소의 lat·lng)")
if not a["jibun"]:
    todo_list.append("지번 주소")
if cfg["photos_temporary"]:
    todo_list.append("사진 — 야놀자·여기어때·에어비앤비 사진. 권리 확인 또는 촬영본 교체 후 photos_temporary=false")
for c in cfg["channels"]:
    if not c["url"]:
        todo_list.append(f"채널 주소 — {c['name']}")
for row, val in cfg["rates"]:
    if not val:
        todo_list.append(f"요금 — {row}")

# ── 사진: images/*.jpg → dist/images/*.webp (1600·800·400) ─────────────────
shutil.rmtree(DIST, ignore_errors=True)
(DIST / "images").mkdir(parents=True)
(DIST / "posts").mkdir()
_size = {}


def prep(stem):
    if stem not in _size:
        src = Image.open(ROOT / "images" / f"{stem}.jpg").convert("RGB")
        for w, suffix in ((1600, ""), (800, "-800"), (400, "-400")):
            im = src.copy()
            im.thumbnail((w, w * 2))
            im.save(DIST / "images" / f"{stem}{suffix}.webp", quality=80, method=6)
        _size[stem] = src.size
    return _size[stem]


def img(stem, alt, sizes="(min-width: 1024px) 50vw, 100vw", eager=False, cls=""):
    w, h = prep(stem)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img{" class=" + chr(34) + cls + chr(34) if cls else ""} src="{base}/images/{stem}-800.webp" '
            f'srcset="{base}/images/{stem}-400.webp 400w, {base}/images/{stem}-800.webp 800w, {base}/images/{stem}.webp 1600w" '
            f'sizes="{sizes}" width="{w}" height="{h}" alt="{escape(alt)}" {load} decoding="async">')


def ai_note(*stems):
    """촬영 전 자리 — AI 시안이면 사진 아래 한 줄. 촬영본으로 바꾸면(ai_images에서 빼면) 사라진다."""
    return '<p class="ai">촬영 예정 자리입니다. 지금 보이는 사진은 AI로 만든 시안입니다.</p>' if cfg["photos_temporary"] and any(s in AI for s in stems) else ""


# 공유 카드 1200x630
og_src = Image.open(ROOT / "images" / f"{cfg['images']['og']}.jpg").convert("RGB")
W, H = og_src.size
h = int(W * 630 / 1200)
og_src.crop((0, (H - h) // 2, W, (H - h) // 2 + h)).resize((1200, 630)).save(DIST / "og.jpg", quality=85)
og_image = f"{base}/og.jpg"

# ── 공통 조각 ───────────────────────────────────────────────────────────
ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
ico_call = ICON.format('<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>')
ico_sms = ICON.format('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>')
ico_pin = ICON.format('<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>')
ico_cal = ICON.format('<rect x="3" y="4" width="18" height="18"/><path d="M16 2v4M8 2v4M3 10h18"/>')
ico_menu = ICON.format('<path d="M3 7h18M3 12h18M3 17h18"/>')
ico_x = ICON.format('<path d="M6 6l12 12M18 6L6 18"/>')
ico_snd = ICON.format('<path d="M11 5 6 9H2v6h4l5 4z"/><g class="w"><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18.5 5.5a9 9 0 0 1 0 13"/></g>')
# 현장 소리(static/ambient.mp3)가 있을 때만 상단에 스피커 버튼 — 자동 재생 아님, 누를 때만 내려받아 재생
snd_btn = f'<button class="snd" type="button" data-src="{base}/ambient.mp3" aria-pressed="false" aria-label="현장 소리 켜기">{ico_snd}</button>' if (ROOT / "static" / "ambient.mp3").exists() else ""
mark = (ROOT / "static" / "favicon.svg").read_text(encoding="utf-8").strip().replace("<svg ", '<svg aria-hidden="true" ', 1)

TOPICS = cfg.get("topics", [])  # 주제별 페이지(유리온실·정원·바비큐) — 검색어 하나에 주소 하나
MENU = [("house.html", "두 채")] + [(f"{t['slug']}.html", t["menu"]) for t in TOPICS] + [("gathering.html", "모임"), ("pet.html", "반려견"), ("guide.html", "이용 안내"), ("around.html", "오시는 길"), ("blog.html", "소식")]
sms_href = f"sms:{sms_tel}?&body={quote(cfg['sms_body'])}" if sms_tel else (book1["url"] if book1 else f"{base}/guide.html#book")
if g["lat"]:
    route_url = f"https://map.kakao.com/link/to/{quote(name)},{g['lat']},{g['lng']}"
else:
    route_url = f"https://map.kakao.com/link/search/{quote(addr)}"
naver_map_url = f"https://map.naver.com/p/search/{quote(addr)}"
filled = [c for c in cfg["channels"] if c["url"]]
css_v = hashlib.md5((ROOT / "static" / "site.css").read_bytes()).hexdigest()[:8]
js_v = hashlib.md5((ROOT / "static" / "site.js").read_bytes()).hexdigest()[:8]
biz = " · ".join(x for x in (f"대표 {cfg['owner']}" if cfg["owner"] else "", f"사업자등록번호 {cfg['biz_no']}" if cfg["biz_no"] else "", cfg.get("permit", "")) if x)
shell = (T / "shell.html").read_text(encoding="utf-8")

# 전화가 있으면 전화·문자, 없으면 예약 채널 링크 — 메뉴 시트·바닥·폰 하단 바·404가 같은 값을 쓴다
if phone:
    sheet_call = f'<a class="call" href="tel:{tel}">전화 {escape(phone)}</a>'
    foot_contact = f'<a href="tel:{tel}">{escape(phone)}</a>'
    bar = f'<a href="tel:{tel}">{ico_call}전화</a><a href="{sms_href}">{ico_sms}문자</a>'
    contact_btn = f'<a class="btn btn-line" href="tel:{tel}">전화 {escape(phone)}</a>'
else:
    sheet_call = "".join(f'<a class="call" href="{escape(b["url"])}" target="_blank" rel="noopener">{escape(b["name"])}에서 예약</a>' for b in booking[:1])
    foot_contact = " · ".join(f'<a href="{escape(b["url"])}" target="_blank" rel="noopener">{escape(b["name"])}</a>' for b in booking) or "예약 문의"
    bar = "".join(f'<a href="{escape(b["url"])}" target="_blank" rel="noopener">{ico_cal}{escape(b["name"])}</a>' for b in booking[:2])
    contact_btn = f'<a class="btn btn-line" href="{escape(book1["url"])}" target="_blank" rel="noopener">{escape(book1["name"])}에서 예약</a>' if book1 else ""


def fill(tpl, v):
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(v[m.group(1)]), tpl)


def ld(*objs):
    return "\n".join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("<", "\\u003c") + "</script>" for o in objs)


def crumbs(path, title):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{base}/"},
        {"@type": "ListItem", "position": 2, "name": title, "item": f"{base}/{path}"}]}


def page(path, title, description, body, lds, og_title=None, extra="", preload="", current=None):
    menu = "".join(f'<a href="{base}/{p}"{" aria-current=" + chr(34) + "page" + chr(34) if p == current else ""}>{t}</a>' for p, t in [("index.html", "처음")] + MENU)
    v = dict(
        robots='<meta name="robots" content="noindex">' if noindex else "",
        title=escape(title), description=escape(description), url=f"{base}/{path}" if path != "index.html" else f"{base}/",
        name=escape(name), og_title=escape(og_title or title), og_image=og_image, base=base,
        verify="".join(f'<meta name="{k}" content="{cfg[c]}">' for k, c in (("google-site-verification", "google_verify"), ("naver-site-verification", "naver_verify")) if cfg[c]),
        css_v=css_v, js_v=js_v, preload=preload, ld=ld(*lds),
        ga4=(f'<script async src="https://www.googletagmanager.com/gtag/js?id={cfg["ga4"]}"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{cfg["ga4"]}");</script>') if cfg["ga4"] else "",
        mark=mark, menu=menu, ico_menu=ico_menu, ico_x=ico_x, ico_pin=ico_pin, snd=snd_btn,
        body=body, addr=escape(addr), checkin=cfg["checkin"], checkout=cfg["checkout"],
        sheet_call=sheet_call, foot_contact=foot_contact, bar=bar,
        foot_menu="".join(f'<li><a href="{base}/{p}">{t}</a></li>' for p, t in MENU),
        channels="".join(f'<li><a href="{escape(c["url"])}" target="_blank" rel="noopener">{escape(c["name"])}</a></li>' for c in filled) or "<li>준비 중</li>",
        biz=(escape(biz) + " · ") if biz else "", year=today.year, updated=today.isoformat(),
        route_url=route_url, extra=extra,
    )
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(fill(shell, v), encoding="utf-8")


def book_form():
    if not sms_tel:  # 전화 전: 예약 채널로 바로
        return ('<div class="ask ask-links">' + "".join(
            f'<a class="btn {"btn-fill" if i == 0 else "btn-line"}" href="{escape(b["url"])}" target="_blank" rel="noopener">{ico_cal}{escape(b["name"])}에서 빈 날짜 보기</a>'
            for i, b in enumerate(booking)) + "</div>")
    opts = "".join(f'<option{" selected" if n == cap["base"] else ""}>{n}</option>' for n in range(2, cap["max"] + 1))
    return (f'<form class="ask" data-name="{escape(name)}" data-sms="{sms_tel}">'
            f'<label><span>입실 날짜</span><input type="date" name="date" min="{today.isoformat()}"></label>'
            f'<label><span>몇 박</span><select name="nights"><option>1</option><option>2</option><option>3</option></select></label>'
            f'<label><span>인원</span><select name="people">{opts}</select></label>'
            f'<button class="btn btn-fill" type="submit">{ico_sms}문자로 빈 날짜 묻기</button></form>')


def faq_html(items):
    return "".join(f'<details><summary>{escape(q)}</summary><p>{escape(ans)}</p></details>' for q, ans in items)


def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in items]}


def qa_html(items, title="궁금한 것"):
    """AEO: 소제목은 질문, 바로 아래 첫 문장이 답. HTML 원문에 글자로 남는다."""
    return (f'<section class="qa"><div class="wrap"><div class="head rv"><h2>{escape(title)}</h2></div><div class="qas">'
            + "".join(f'<article class="rv"><h3>{escape(q)}</h3><p>{escape(ans)}</p></article>' for q, ans in items) + "</div></div></section>") if items else ""


rates_rows = "".join(f'<tr><th>{escape(r)}</th>{"<td>" + escape(v) + "</td>" if v else "<td class=" + chr(34) + "ask" + chr(34) + ">문의</td>"}</tr>' for r, v in cfg["rates"])
extras_html = "".join(f'<div><b>{escape(k)}</b><span>{escape(v)}</span></div>' for k, v in cfg["extras"])
seats_html = "".join(f'<div class="rv"><b>{escape(n)}</b><p>{escape(d)}</p></div>' for n, d in cfg["gathering"]["seats"])
around_html = "".join(f'<div><div><b>{escape(n)}</b><span>{escape(d)}</span></div><em>{escape(m)}</em></div>' for n, d, m in cfg["around"])
# 실제 출처 평점만, 출처·날짜와 함께 (자체 평점·schema 없음)
ratings_html = "".join(f'<p class="rating rv"><b>{escape(s)}</b> <a href="{escape(u)}" target="_blank" rel="noopener">{escape(src)} {escape(d)}</a> <small>{escape(dt)} 기준</small></p>'
                       for src, s, d, u, dt in cfg.get("ratings", []))

# ── 블로그 글(글해줌 연결) ─────────────────────────────────────────────────
posts_path = ROOT / "posts.json"
posts = json.loads(posts_path.read_text(encoding="utf-8")) if posts_path.exists() else []
posts = sorted([x for x in posts if isinstance(x, dict) and x.get("id")], key=lambda x: -int(x["id"]))
plain = lambda t, n: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(t or ""))).strip()[:n]


def post_card(x):
    return (f'<article class="post rv"><time datetime="{escape(str(x["date"]))}">{escape(str(x["date"]))}</time>'
            f'<h3><a href="{base}/posts/{x["id"]}.html">{escape(x["title"])}</a></h3><p>{escape(plain(x.get("summary") or x.get("content"), 110))}</p>'
            f'<a class="go" href="{base}/posts/{x["id"]}.html">읽기</a></article>')


# ── 첫 화면 ───────────────────────────────────────────────────────────────
hero, hero_m = cfg["images"]["hero"], cfg["images"]["hero_m"]
hw, hh = prep(hero)
mw, mh = prep(hero_m)
hero_pic = (f'<picture><source media="(max-width: 719px)" srcset="{base}/images/{hero_m}-800.webp 800w, {base}/images/{hero_m}.webp 1600w" sizes="100vw">'
            f'<img src="{base}/images/{hero}-800.webp" srcset="{base}/images/{hero}-800.webp 800w, {base}/images/{hero}.webp 1600w" sizes="100vw" '
            f'width="{hw}" height="{hh}" alt="{escape(cfg["hero_alt"])}" fetchpriority="high" decoding="async"></picture>')
preload = (f'<link rel="preload" as="image" href="{base}/images/{hero}-800.webp" imagesrcset="{base}/images/{hero}-800.webp 800w, {base}/images/{hero}.webp 1600w" imagesizes="100vw" media="(min-width: 720px)">'
           f'<link rel="preload" as="image" href="{base}/images/{hero_m}-800.webp" media="(max-width: 719px)">')

three_html = ""
for i, (word, title, text, stem) in enumerate(cfg["three"]):
    fig = (f'<figure class="rv{" big" if i == 0 else ""}">{img(stem, f"{name} {title}", "(min-width: 1024px) 58vw, 100vw" if i == 0 else "(min-width: 1024px) 40vw, 100vw")}'
           f'<figcaption><span class="word">{escape(word)}</span><h3>{escape(title)}</h3><p>{escape(text)}</p>{ai_note(stem)}</figcaption></figure>')
    if i == 0:
        three_html += fig + '<div class="side">'
    else:
        three_html += fig
three_html += "</div>"

day_html = ""
for i, (t, label, title, text, p1, p2) in enumerate(cfg["day"], 1):
    if i == 2:  # 거실: 스크롤 따라 훑기
        pics = f'<div class="pan"><div class="stick">{img(p1, f"{name} 거실, 천장 조명부터 창밖 호수까지", "100vw")}</div></div>'
    else:
        pics = f'<div class="pics">{img(p1, f"{name} {label} {title}", "(min-width: 1024px) 60vw, 100vw")}{img(p2, f"{name} {label} 풍경", "(min-width: 1024px) 40vw, 100vw") if p2 else ""}</div>'
    day_html += (f'<article class="moment m{i}"><div class="t"><b>{escape(t)}</b><span>{escape(label)}</span></div>'
                 f'<div class="rv">{pics}<h3>{escape(title)}</h3><p class="txt">{escape(text)}</p>{ai_note(p1, p2)}</div></article>')

seasons_html = "".join(f'<figure>{img(stem, f"{name} {s} {d}", "(min-width: 720px) 520px, 78vw")}<figcaption><b>{escape(s)}</b><span>{escape(d)}</span></figcaption></figure>'
                       for s, d, stem in cfg["seasons"])
pet = cfg["pet"]
gath = cfg["gathering"]
cov = cfg["covers"]
cw, ch = prep(cov["gathering_home"])
description = cfg["description"]
posts_section = (f'<section><div class="wrap"><div class="head rv"><h2>소식</h2></div><div class="posts">{"".join(post_card(x) for x in posts[:3])}</div>'
                 f'<p class="rv" style="margin-top:30px"><a class="link" href="{base}/blog.html">글 전체 보기</a></p></div></section>') if posts else ""

index_body = fill((T / "index.html").read_text(encoding="utf-8"), dict(
    hero_pic=hero_pic, tagline="".join(f"<span><i>{escape(l.strip())}</i></span>" for l in cfg["tagline"].split("|")),
    hero_label=escape(cfg["hero_label"]), hero_sub=escape(cfg["hero_sub"]),
    hero_cap=f'<p class="cap">촬영 예정 자리, AI 시안</p>' if hero in AI and cfg["photos_temporary"] else "",
    name=escape(name), today=today.isoformat(),
    cap_max=cap["max"], cap_base=cap["base"],
    statement=escape(cfg["statement"]), declare_sub=escape(cfg["declare_sub"]), ratings_html=ratings_html,
    quote=escape(cfg["quote"][0]), quote_by=escape(cfg["quote"][1]), book_form=book_form(),
    three_html=three_html, day_lead=escape(cfg["day_lead"]), day_html=day_html,
    base=base, cover_img=cov["gathering_home"], cover_w=cw, cover_h=ch, cover_alt=escape(f"{name} 유리온실 식탁, 호수 쪽으로 열린 유리문"),
    g_title=escape(gath["title"]), g_lead=escape(gath["lead"]), seats_html=seats_html,
    pet_img=img(pet["photos"][0], f"{name} 정원 대문과 장미 아치", "(min-width: 720px) 45vw, 100vw"), pet_title=escape(pet["title"]), pet_lead=escape(pet["lead"]),
    pet_rules="".join(f'<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in pet["rules"][:3]), pet_kids=escape(pet["kids"]),
    seasons_html=seasons_html, checkin=cfg["checkin"], checkout=cfg["checkout"], rates_rows=rates_rows, rate_note=escape(cfg["rate_note"]),
    extras_html=extras_html, faq_html=faq_html(cfg["faq"]), addr=escape(addr), route_url=route_url, naver_map_url=naver_map_url,
    nearby_line=escape(", ".join(f"{n} {d}" for n, d in cfg["nearby"])), around_html=around_html, around_note=escape(cfg["around_note"]),
    posts_section=posts_section))

business = {
    "@context": "https://schema.org", "@type": "LodgingBusiness", "additionalType": "https://schema.org/VacationRental",
    "name": name, "alternateName": cfg["name_alt"], "description": description,
    "address": {"@type": "PostalAddress", "streetAddress": a["street"], "addressLocality": a["city"], "addressRegion": a["region"], "addressCountry": "KR"},
    "checkinTime": cfg["checkin"], "checkoutTime": cfg["checkout"], "petsAllowed": True, "image": og_image,
    "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": n, "value": v} for n, v in cfg["amenities"]],
}
if phone:
    business["telephone"] = "+82-" + phone.lstrip("0")
if g["lat"]:
    business["geo"] = {"@type": "GeoCoordinates", "latitude": g["lat"], "longitude": g["lng"]}
if domain:
    business["url"] = domain + "/"
if filled:
    business["sameAs"] = [c["url"] for c in filled]
page("index.html", f"{name} | 청풍호 앞 독채 펜션, 벽돌집과 유리온실, 하루 한 가족 최대 {cap['max']}명", description, index_body,
     [business, faq_ld(cfg["faq"])], og_title=f"{name}, {cfg['tagline'].replace('|', ' ')}", preload=preload)

# ── 두 채 ─────────────────────────────────────────────────────────────────
rooms_html, gallery = "", []
for title, text, stems in cfg["house_rooms"]:
    btns = ""
    for i, s in enumerate(stems):
        prep(s)
        btns += f'<button type="button" data-full="{base}/images/{s}.webp" aria-label="{escape(title)} 사진 크게 보기">{img(s, f"{name} {title} {i + 1}", "(min-width: 1024px) 60vw, 100vw" if i == 0 else "(min-width: 1024px) 20vw, 50vw")}</button>'
        gallery.append({"@type": "ImageObject", "contentUrl": f"{base}/images/{s}.webp", "name": f"{name} {title}"})
    rooms_html += f'<article class="room"><div class="info rv"><h2>{escape(title)}</h2><p>{escape(text)}</p>{ai_note(*stems)}</div><div class="g rv">{btns}</div></article>'
house_body = (f'<div class="page"><div class="wrap phead"><h1>{escape(cfg["house_title"])}</h1><p class="lead">{escape(cfg["house_lead"])}</p></div>'
              f'<div class="pcover">{img(cov["house"], f"{name} 벽돌집 정면, 주황 기와와 잔디 마당", "100vw", eager=True)}</div>'
              f'<div class="wrap" style="padding-top:clamp(60px,8vw,110px);padding-bottom:clamp(80px,10vw,140px)"><div class="rooms">{rooms_html}</div>'
              f'<p class="small" style="margin-top:40px">{escape(cfg["house_note"])}</p></div>{qa_html(cfg.get("house_qa", []), "집에 대해 자주 묻는 것")}</div>')
page("house.html", f"두 채 | {name}", f"{name}의 벽돌집 거실, 주방, 침실 3개, 욕실 2개와 유리온실 '가든치유', 300평 정원. 두 채를 하루 한 가족이 씁니다.",
     house_body, [{"@context": "https://schema.org", "@type": "ImageGallery", "name": f"{name} 공간 사진", "url": f"{base}/house.html", "image": gallery}, faq_ld(cfg.get("house_qa", [])), crumbs("house.html", "두 채")],
     extra='<dialog class="lb"><button type="button" aria-label="닫기">×</button><img src="" alt=""></dialog>', current="house.html")

# ── 주제별 페이지: 유리온실·정원·바비큐 (config topics) ─────────────────────
for tp in TOPICS:
    path = f"{tp['slug']}.html"
    tgal = "".join(f'<figure class="rv">{img(s, f"{name} {tp["title"]} {i + 1}", "(min-width: 720px) 33vw, 100vw")}</figure>' for i, s in enumerate(tp["photos"]))
    tbody = (f'<div class="page"><div class="wrap phead"><h1>{escape(tp["h1"])}</h1><p class="lead">{escape(tp["lead"])}</p></div>'
             f'<div class="pcover">{img(tp["cover"], tp["cover_alt"], "100vw", eager=True)}</div>'
             + qa_html(tp["qa"], f"{tp['title']}, 묻고 답하기")
             + f'<section><div class="wrap"><div class="gl">{tgal}</div></div></section>'
             f'<section id="book"><div class="wrap"><div class="head rv"><h2>날짜를 먼저 확인하세요</h2><p class="lead">하루 한 가족만 받습니다. 빈 날짜는 예약 채널에서 바로 보입니다.</p></div><div class="book" style="border:1px solid var(--line)"><div class="wrap">{book_form()}</div></div></div></section></div>')
    page(path, f"{tp['title']} | {name}", tp["description"], tbody,
         [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} {tp['title']}", "url": f"{base}/{path}", "description": tp["description"]},
          faq_ld(tp["qa"]),
          {"@context": "https://schema.org", "@type": "ImageGallery", "name": f"{name} {tp['title']} 사진", "url": f"{base}/{path}",
           "image": [{"@type": "ImageObject", "contentUrl": f"{base}/images/{s}.webp", "name": f"{name} {tp['title']}"} for s in [tp["cover"]] + tp["photos"]]},
          crumbs(path, tp["menu"])], current=path)

# ── 모임 ─────────────────────────────────────────────────────────────────
gl = "".join(f'<figure class="rv">{img(s, f"{name} 모임 {i + 1}", "(min-width: 720px) 33vw, 100vw")}</figure>' for i, s in enumerate(gath["photos"]))
gath_body = (f'<div class="page"><div class="wrap phead"><h1>{escape(gath["title"])}</h1><p class="lead">{escape(gath["lead"])}</p></div>'
             f'<div class="pcover">{img(cov["gathering"], f"{name} 유리온실에 차린 칠순 생일상과 풍선", "100vw", eager=True)}</div>'
             f'<div class="wrap" style="padding-top:clamp(40px,5vw,64px)">{ai_note(cov["gathering"])}<div class="seats">{seats_html}</div>'
             f'<ul class="points">{"".join(f"<li>{escape(p)}</li>" for p in gath["points"])}</ul></div>'
             f'<section><div class="wrap"><div class="gl">{gl}</div></div></section>'
             + qa_html(cfg.get("gathering_qa", []), "모임 전에 묻는 것")
             + f'<section id="book"><div class="wrap"><div class="head rv"><h2>모임 날짜를 먼저 잡아 두세요</h2><p class="lead">하루 한 가족이라 주말과 연휴는 일찍 찹니다. 후기에 "1년 전부터 예약해야겠다"는 말이 나올 만큼입니다.</p></div><div class="book" style="border:1px solid var(--line)"><div class="wrap">{book_form()}</div></div></div></section></div>')
page("gathering.html", f"환갑, 칠순, 생일 모임 | {name}", f"{name}에서 열 명까지 모이는 가족 행사. 유리온실에 차리는 생일상과 칠순상, 떠나는 날 아침 가족사진. 하루 한 가족이라 조용히 모입니다.",
     gath_body, [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 모임 안내", "url": f"{base}/gathering.html", "description": gath["lead"]}, faq_ld(cfg.get("gathering_qa", [])), crumbs("gathering.html", "모임")], current="gathering.html")

# ── 반려견 ───────────────────────────────────────────────────────────────
pet_body = (f'<div class="page"><div class="wrap phead"><h1>{escape(pet["title"])}</h1><p class="lead">{escape(pet["lead"])}</p></div>'
            f'<section style="padding-top:0;border-top:0"><div class="wrap"><div class="split"><figure class="rv">{img(pet["photos"][1], f"{name} 디딤돌 길과 호수", "(min-width: 720px) 45vw, 100vw", eager=True)}</figure>'
            f'<div><dl class="rules rv">{"".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in pet["rules"])}</dl><p class="kids rv">{escape(pet["kids"])}</p></div></div></div></section>'
            f'<section><div class="wrap"><div class="gl">{"".join(f"<figure class=" + chr(34) + "rv" + chr(34) + f">{img(s, f"{name} 정원 {i + 1}", "(min-width: 720px) 33vw, 100vw")}</figure>" for i, s in enumerate(pet["gallery"]))}</div></div></section>'
            + qa_html(cfg.get("pet_qa", []), "반려견 동반 전에 묻는 것") + "</div>")
page("pet.html", f"반려견 동반 | {name}", f"{name}은 10kg 이하 반려견 2마리까지 무료로 함께 옵니다. 대문과 울타리가 있는 300평 정원에서 자유롭게, 침실과 침구는 출입하지 않습니다. 고양이는 불가.",
     pet_body, [{"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 반려견 안내", "url": f"{base}/pet.html", "description": pet["lead"]}, faq_ld(cfg.get("pet_qa", [])), crumbs("pet.html", "반려견")], current="pet.html")

# ── 이용 안내 ────────────────────────────────────────────────────────────
guide_body = (f'<div class="page"><div class="wrap phead"><h1>요금과 이용 안내</h1><p class="lead">기준 인원 {cap["base"]}명, 최대 {cap["max"]}명. 입실 {cfg["checkin"]}, 퇴실 {cfg["checkout"]}. 빈 날짜와 요금은 예약 채널에서 바로 확인됩니다.</p></div>'
              f'<div class="book" id="book" style="border-top:1px solid var(--line)"><div class="wrap">{book_form()}</div></div>'
              f'<section><div class="wrap"><div class="rates"><div><h2 style="margin-bottom:20px">1박 요금</h2><table>{rates_rows}</table><p class="note">{escape(cfg["rate_note"])}</p></div>'
              f'<div><h2 style="margin-bottom:20px">추가 요금</h2><div class="extras">{extras_html}</div></div></div></div></section>'
              f'<section><div class="wrap"><div class="head"><h2>이용 규칙</h2></div><dl class="rules" style="max-width:46em">{"".join(f"<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>" for k, v in cfg["rules"])}</dl></div></section>'
              f'<section><div class="wrap"><div class="head"><h2>자주 묻는 질문</h2></div><div class="faq">{faq_html(cfg["faq"])}</div></div></section></div>')
page("guide.html", f"요금과 이용 안내 | {name}", f"{name} 1박 요금, 인원 추가와 숯불 바비큐, 불멍 장작 요금, 입실과 퇴실 시간, 이용 규칙. 기준 {cap['base']}명 최대 {cap['max']}명.",
     guide_body, [faq_ld(cfg["faq"]), crumbs("guide.html", "이용 안내")], current="guide.html")

# ── 오시는 길 ────────────────────────────────────────────────────────────
# 제천에서 머무는 법 — config "jecheon" (십경·축제와 문화·먹을 곳·공식 안내). 값은 공식 페이지에서 확인한 것만, 빈 절은 안 나옴
J = cfg.get("jecheon", {})
ext = lambda items: ('<div class="ext">' + "".join(
    f'<a href="{escape(u)}" target="_blank" rel="noopener"><span><b>{escape(n)}</b><span>{escape(d)}</span></span><small>{escape(re.sub(r"^https?://(www\.)?", "", u).split("/")[0])}</small></a>'
    for n, d, u in items) + "</div>") if items else ""


def jsec(title, lead, body):
    return f'<section class="jsec"><div class="wrap"><div class="head"><h2>{escape(title)}</h2>{"<p class=" + chr(34) + "lead" + chr(34) + ">" + escape(lead) + "</p>" if lead else ""}</div>{body}</div></section>' if body else ""


ten_html = ('<ol class="ten">' + "".join(f'<li><span><b>{"<a href=" + chr(34) + escape(u) + chr(34) + " target=" + chr(34) + "_blank" + chr(34) + " rel=" + chr(34) + "noopener" + chr(34) + ">" + escape(n) + "</a>" if u else escape(n)}</b><span>{escape(d)}</span></span><em>{escape(m)}</em></li>' for n, d, m, u in J.get("ten", [])) + "</ol>"
            + (f'<p class="jnote"><a class="link" href="{escape(J["ten_url"])}" target="_blank" rel="noopener">제천시 문화관광 누리집의 제천 10경 안내</a></p>' if J.get("ten_url") else "")) if J.get("ten") else ""
food_html = ((f'<p class="jnote" style="margin:0 0 22px">{escape(J["food_intro"])}</p>' if J.get("food_intro") else "") + ext(J.get("food", []))) if J.get("food") else ""
around_body = (f'<div class="page"><div class="wrap phead"><h1>청풍호 앞, 제천에서 머무는 법</h1><p class="lead">{escape(addr)}. {escape(cfg["around_lead"])}</p>'
               f'<div class="maps"><a class="btn btn-fill" href="{route_url}" target="_blank" rel="noopener">카카오맵 길찾기</a><a class="btn btn-line" href="{naver_map_url}" target="_blank" rel="noopener">네이버 지도</a></div></div>'
               f'<div class="pcover">{img(cov["around"], f"{name} 정원 끝 울타리 너머 청풍호", "100vw", eager=True)}</div>'
               f'<section class="jsec" style="border-top:0"><div class="wrap"><div class="head"><h2>집에서 차로</h2><p class="lead">{escape(cfg["around_note"])}</p></div><div class="around">{around_html}</div></div></section>'
               + jsec("제천 10경", J.get("ten_lead", ""), ten_html)
               + jsec("축제와 문화", J.get("culture_lead", ""), ext(J.get("culture", [])))
               + jsec("먹을 곳", J.get("food_lead", ""), food_html)
               + jsec("공식 안내", J.get("links_lead", ""), ext(J.get("links", [])))
               + "</div>")
around_ld = {"@context": "https://schema.org", "@type": "WebPage", "name": f"{name} 오시는 길과 제천 안내", "url": f"{base}/around.html",
             "description": f"{addr}. 제천 10경, 축제와 문화, 먹을 곳, 공식 안내 링크"}
if J.get("ten"):
    around_ld["mainEntity"] = {"@type": "ItemList", "name": "제천 10경", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "description": d} for i, (n, d, _, _u) in enumerate(J["ten"], 1)]}
page("around.html", f"오시는 길과 제천 안내 | {name}", f"{name} 오시는 길. {addr}. 차로 3분의 능강계곡, 정방사와 옥순봉 출렁다리, 제천 10경, 음악영화제와 문화유산단지, 약채락 먹을 곳, 제천시 공식 안내.",
     around_body, [around_ld, crumbs("around.html", "오시는 길")], current="around.html")

# ── 블로그: posts.json → blog.html, posts/N.html (글해줌이 가장 큰 번호 글을 견본으로 복제) ──
for x in posts:
    title, content, date = x["title"], x.get("content") or "", str(x.get("date") or today)[:10]
    desc = plain(x.get("summary") or content, 150)
    url = f"{base}/posts/{x['id']}.html"
    m = re.search(r'<img[^>]+src="([^"]+)"', content)
    image = (base + "/" + m.group(1)[3:]) if m and m.group(1).startswith("../") else (m.group(1) if m else og_image)
    tags = "".join(f'<span class="blog-tag">#{escape(t)}</span> ' for t in x.get("tags") or [])
    body = (f'<div class="page"><article class="wrap" style="max-width:820px"><header class="phead"><p class="blog-post-meta small"><time datetime="{date}">{date}</time></p>'
            f'<h1>{escape(title)}</h1><p class="blog-card-tags small">{tags}</p></header>'
            f'<div class="blog-post-content" style="padding-bottom:clamp(80px,10vw,140px)">{content}</div>'
            f'<p style="padding-bottom:80px"><a class="link" href="{base}/blog.html">소식 목록으로</a></p></article></div>')
    lds = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "image": image, "datePublished": date, "dateModified": date,
            "author": {"@type": "Organization", "name": name}, "publisher": {"@type": "Organization", "name": name, "logo": {"@type": "ImageObject", "url": f"{base}/favicon.svg"}},
            "mainEntityOfPage": url, "keywords": ", ".join((x.get("tags") or [])[:5]) or title},
           {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{base}/"}, {"@type": "ListItem", "position": 2, "name": "소식", "item": f"{base}/blog.html"},
               {"@type": "ListItem", "position": 3, "name": title, "item": url}]}]
    page(f"posts/{x['id']}.html", f"{title} | {name}", desc, body, lds, current="blog.html")
    shutil.copy(DIST / "posts" / f"{x['id']}.html", ROOT / "posts" / f"{x['id']}.html")  # 저장소에도 둠 — 글해줌 견본
blog_body = (f'<div class="page"><div class="wrap phead"><h1>소식</h1><p class="lead">{escape(cfg.get("blog_lead") or "정원의 꽃 소식과 청풍호 계절, 온실에서 차린 상을 적습니다.")}</p></div>'
             f'<section style="padding-top:0;border-top:0"><div class="wrap"><div class="posts">{"".join(post_card(x) for x in posts) or "<p>첫 글을 준비하고 있습니다.</p>"}</div></div></section></div>')
page("blog.html", f"소식 | {name}", f"{name} 소식과 정원의 꽃, 청풍호 계절 안내 글.", blog_body,
     [{"@context": "https://schema.org", "@type": "CollectionPage", "name": f"{name} 소식", "url": f"{base}/blog.html", "inLanguage": "ko-KR",
       "hasPart": [{"@type": "Article", "headline": x["title"], "url": f"{base}/posts/{x['id']}.html", "datePublished": str(x["date"])[:10]} for x in posts]}, crumbs("blog.html", "소식")], current="blog.html")
if posts_path.exists():
    shutil.copy(posts_path, DIST / "posts.json")
if (ROOT / "images" / "posts").is_dir():
    shutil.copytree(ROOT / "images" / "posts", DIST / "images" / "posts")

# ── 404 ──────────────────────────────────────────────────────────────────
page("404.html", f"페이지를 찾을 수 없습니다 | {name}", "주소가 바뀌었거나 잘못 적혔을 수 있습니다.",
     f'<div class="page"><div class="wrap phead"><h1>그 주소에는 페이지가 없습니다</h1><p class="lead">주소가 바뀌었거나 잘못 적혔을 수 있습니다.</p>'
     f'<div class="maps"><a class="btn btn-fill" href="{base}/">처음으로</a>{contact_btn}</div></div></div>', [])
(DIST / "404.html").write_text((DIST / "404.html").read_text(encoding="utf-8").replace('<meta name="robots" content="noindex">', "", 1).replace("<title>", '<meta name="robots" content="noindex">\n<title>', 1), encoding="utf-8")

# ── llms.txt · robots · sitemap · 기타 ─────────────────────────────────────
nl = "\n"
(DIST / "llms.txt").write_text(f"""# {name}

> {cfg['llms_intro']}

## 기본 정보
- 상호: {name} (다른 표기: {', '.join(cfg['name_alt'])})
- 주소: {addr}{(' (지번 ' + a['jibun'] + ')') if a['jibun'] else ''}
- 전화: {phone or '예약 채널로 문의 — ' + ', '.join(f"{b['name']} {b['url']}" for b in booking)}
- 입실 {cfg['checkin']} · 퇴실 {cfg['checkout']}
- 인원: 기준 {cap['base']}명, 최대 {cap['max']}명 (초과 1명당 {cap['extra_fee']})
- 구조: 벽돌집 {cfg['house_area']} (침실 {cfg['bedrooms']}개, 침대 {cfg['beds']}개, 욕실 {cfg['baths']}개) + 유리온실 '가든치유', 정원 {cfg['site_area']}
{nl.join(f"- 평점: {src} {s} ({d}, {dt} 기준) {u}" for src, s, d, u, dt in cfg.get('ratings', []))}

## 요금 (1박)
{nl.join(f"- {r}: {v or '문의'}" for r, v in cfg['rates'])}
- {cfg['rate_note']}
{nl.join(f"- {k}: {v}" for k, v in cfg['extras'])}

## 두 채
{nl.join(f"- {t}: {d}" for t, d, _ in cfg['house_rooms'])}

{nl.join(f"## {t['title']}{nl}- {t['lead']}{nl}" + nl.join(f"- Q. {q}{nl}  A. {ans}" for q, ans in t['qa']) for t in TOPICS)}

## 모임
- {gath['lead']}
{nl.join(f"- {n}: {d}" for n, d in gath['seats'])}
{nl.join(f"- {p}" for p in gath['points'])}

## 반려견
{nl.join(f"- {k}: {v}" for k, v in pet['rules'])}

## 이용 규칙
{nl.join(f"- {k}: {v}" for k, v in cfg['rules'])}

## 가까운 곳 (차로)
{nl.join(f"- {n}: {d}, 약 {m}" for n, d, m in cfg['around'])}

## 자주 묻는 질문
{nl.join(f"- Q. {q}{nl}  A. {ans}" for q, ans in cfg['faq'])}

## 채널
{nl.join(f"- {c['name']}: {c['url']}" for c in filled)}

## 글 목록
{nl.join(f"- [{plain(x['title'], 120)}]({base}/posts/{x['id']}.html): {plain(x.get('summary') or x.get('content'), 140)}" for x in posts[:100])}
""", encoding="utf-8")
(DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n" + (f"Sitemap: {domain}/sitemap.xml\n" if domain and not noindex else ""), encoding="utf-8")
if domain and not noindex:
    urls = [(f"{domain}/", today)] + [(f"{domain}/{p}", today) for p, _ in MENU] + [(f"{domain}/posts/{x['id']}.html", str(x['date'])[:10]) for x in posts]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n", encoding="utf-8")
for k in ROOT.glob("*.txt"):
    if re.fullmatch(r"[0-9a-f]{32}", k.stem):
        shutil.copy(k, DIST / k.name)
for f in (ROOT / "static").iterdir():
    shutil.copy(f, DIST / f.name)
(DIST / ".nojekyll").write_text("", encoding="utf-8")

print(f"완성: {DIST} · 페이지 {len(MENU) + 2}개 · 글 {len(posts)}편")
if noindex:
    print("※ 검색 노출 막힘(noindex) — 도메인이 비었거나 임시 사진이라서. 둘 다 정리되면 자동으로 풀립니다.")
print(f"\n[확인 필요] {len(todo_list)}개")
for t in dict.fromkeys(todo_list):
    print(" -", t)

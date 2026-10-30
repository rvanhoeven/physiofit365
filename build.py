#!/usr/bin/env python3
"""Static site generator for PhysioFit365.

Reads content/{en,nl,es}.json and writes the multilingual site to site/<lang>/...
English is the base language (content/en.json); nl and es must have the same keys.

Usage:  python3 build.py            # build into ./site
        BASE_URL=https://example.com python3 build.py
"""
import json
import os
import re
import shutil
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BASE_URL = os.environ.get("BASE_URL", "https://www.physiofit365.com").rstrip("/")
LANGS = ["en", "nl", "es"]          # en = base language
PAGES = ["home", "about", "services", "faq", "contact", "privacy"]
PATHS = {"home": "", "about": "about/", "services": "services/", "faq": "faq/", "contact": "contact/", "privacy": "privacy/"}

PHONE_DISPLAY = "+34 686 04 22 00"
PHONE_TEL = "+34686042200"
EMAIL = "info@physiofit365.com"
FACEBOOK = "https://www.facebook.com/physiofit365"
INSTAGRAM = "https://www.instagram.com/physiofit365"

ICONS = {
    "manual": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 11V5.5a1.5 1.5 0 0 1 3 0V10m0-1V4a1.5 1.5 0 0 1 3 0v5m0-3.5a1.5 1.5 0 0 1 3 0V11m0-3a1.5 1.5 0 0 1 3 0v6a7 7 0 0 1-7 7h-1a7 7 0 0 1-5.6-2.8L4 14.5a1.6 1.6 0 0 1 2.5-2L7 13"/></svg>',
    "work": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/></svg>',
    "sport": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="14" cy="4.5" r="2"/><path d="m8 21 3-6 3 2v4M6 12l4-3 3 1 3 3 3 1M10 9l-1 6"/></svg>',
    "check": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
    "home": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8M5 10v10h14V10M10 20v-6h4v6"/></svg>',
    "badge": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="5.5"/><path d="m9 14 -1.5 7L12 18.5 16.5 21 15 14"/></svg>',
    "team": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="8" r="3.2"/><circle cx="17" cy="9" r="2.4"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M15.5 14.2c3 .2 5.5 2.4 5.5 5.8"/></svg>',
    "star": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/></svg>',
    "target": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/></svg>',
    "user": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
}
ADV_ICONS = ["user", "home", "badge", "team", "star", "target"]


def load(lang):
    with open(ROOT / "content" / f"{lang}.json", encoding="utf-8") as f:
        return json.load(f)


def check_keys(base, other, path=""):
    """Fail the build if a translation is missing keys that exist in English."""
    problems = []
    if isinstance(base, dict):
        for k in base:
            if k not in other:
                problems.append(f"{path}/{k}")
            else:
                problems += check_keys(base[k], other[k], f"{path}/{k}")
    elif isinstance(base, list):
        if len(base) != len(other):
            problems.append(f"{path} (list length {len(other)} != {len(base)})")
        else:
            for i, (b, o) in enumerate(zip(base, other)):
                problems += check_keys(b, o, f"{path}[{i}]")
    return problems


class Ctx:
    def __init__(self, lang, page, t):
        self.lang, self.page, self.t = lang, page, t
        depth = 0 if page == "home" else 1
        self.up = "../" * (1 + depth)          # from this page back to site root

    def url(self, page, lang=None):
        return f"{self.up}{lang or self.lang}/{PATHS[page]}"

    def asset(self, p):
        return f"{self.up}assets/{p}"


def photo(ctx, mode="lazy"):
    """Mellany's photo. Drop it at site/assets/img/mellany.jpg; until then show a branded placeholder."""
    if (SITE / "assets" / "img" / "mellany.jpg").exists():
        extra = ' fetchpriority="high"' if mode == "eager" else ' loading="lazy"'
        return (f'<img src="{ctx.asset("img/mellany.jpg")}" alt="Mellany Ginny van Hoeven" '
                f'width="460" height="365"{extra}>')
    return (f'<div class="photo-placeholder" role="img" aria-label="Mellany Ginny van Hoeven">'
            f'<img src="{ctx.asset("img/logo.png")}" alt="" width="260"></div>')


def abs_url(lang, page):
    return f"{BASE_URL}/{lang}/{PATHS[page]}"


def head(ctx, title, description):
    t = ctx.t
    full_title = f"{title} | {t['site_name']}" if ctx.page != "home" else f"{t['site_name']} – {title}"
    alts = "\n".join(
        f'<link rel="alternate" hreflang="{l}" href="{abs_url(l, ctx.page)}">' for l in LANGS
    )
    return f"""<!doctype html>
<html lang="{ctx.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{abs_url(ctx.lang, ctx.page)}">
{alts}
<link rel="alternate" hreflang="x-default" href="{abs_url('en', ctx.page)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(t['site_name'])}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:url" content="{abs_url(ctx.lang, ctx.page)}">
<meta property="og:image" content="{BASE_URL}/assets/img/logo.png">
<meta name="theme-color" content="#fe26ac">
<link rel="icon" href="{ctx.asset('img/favicon.svg')}" type="image/svg+xml">
<link rel="icon" href="{ctx.asset('img/favicon.ico')}" sizes="48x48">
<link rel="apple-touch-icon" href="{ctx.asset('img/apple-touch-icon.png')}">
<link rel="stylesheet" href="{ctx.asset('css/style.css')}">
</head>"""


def cur(cond, val):
    return f' aria-current="{val}"' if cond else ""


def header(ctx):
    t = ctx.t
    nav_items = ["home", "about", "services", "faq", "contact"]
    links = "".join(
        f'<li><a href="{ctx.url(p)}"{cur(p == ctx.page, "page")}>{e(t["nav"][p])}</a></li>'
        for p in nav_items
    )
    langs = "".join(
        f'<a href="{ctx.url(ctx.page, l)}" hreflang="{l}" lang="{l}"{cur(l == ctx.lang, "true")} '
        f'title="{e(LANG_NAMES[l])}">{l.upper()}</a>'
        for l in LANGS
    )
    return f"""<body>
<a class="skip" href="#main">{e(t['common']['skip'])}</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="{ctx.url('home')}" aria-label="{e(t['site_name'])} – {e(t['nav']['home'])}">
      <img src="{ctx.asset('img/logo.png')}" alt="{e(t['site_name'])}" width="132" height="74">
    </a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">
      <span class="sr">{e(t['nav']['menu'])}</span><span class="bars" aria-hidden="true"></span>
    </button>
    <nav id="nav" class="nav" aria-label="{e(t['nav']['menu'])}">
      <ul>{links}</ul>
      <div class="lang" role="group" aria-label="{e(t['nav']['language'])}">{langs}</div>
      <a class="btn btn-sm" href="{ctx.url('contact')}">{e(t['nav']['cta'])}</a>
    </nav>
  </div>
</header>
<main id="main">
"""


def footer(ctx):
    t, c = ctx.t, ctx.t["common"]
    cols = "".join(
        f'<li><a href="{ctx.url(p)}">{e(t["nav"][p])}</a></li>' for p in ["home", "about", "services", "faq", "contact"]
    )
    return f"""</main>
<footer class="site-footer">
  <div class="wrap grid">
    <div>
      <img class="foot-icon" src="{ctx.asset('img/icon-large.jpg')}" alt="" width="64">
      <p class="foot-tag">{e(c['tagline'])}</p>
      <p class="social"><a href="{FACEBOOK}" rel="noopener">Facebook</a> · <a href="{INSTAGRAM}" rel="noopener">Instagram</a></p>
    </div>
    <div>
      <h2>{e(t['nav']['menu'])}</h2>
      <ul class="plain">{cols}</ul>
    </div>
    <div>
      <h2>{e(c['hours_label'])}</h2>
      <p>{e(c['hours'])}<br>{e(c['closed'])}</p>
      <p>{e(c['area'])}</p>
    </div>
    <div>
      <h2>{e(t['nav']['contact'])}</h2>
      <p>{e(c['address'])}</p>
      <p><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </div>
  </div>
  <div class="wrap legal">
    <span>© {2026} PhysioFit365. {e(c['rights'])}</span>
    <a href="{ctx.url('privacy')}">{e(c['privacy'])}</a>
  </div>
</footer>
<script src="{ctx.asset('js/site.js')}" defer></script>
</body>
</html>
"""


LANG_NAMES = {"en": "English", "nl": "Nederlands", "es": "Español"}


def ico(name):
    return f'<span class="ico">{ICONS[name]}</span>'


def cta_band(ctx, title, text, label):
    return f"""<section class="band-cta">
  <div class="wrap">
    <h2>{e(title)}</h2>
    <p>{e(text)}</p>
    <a class="btn btn-light" href="{ctx.url('contact')}">{e(label)}</a>
  </div>
</section>
"""


def testimonials(ctx):
    cards = "".join(
        f"""<figure class="quote">
  <blockquote><p>{e(q['quote'])}</p></blockquote>
  <figcaption><strong>{e(q['name'])}</strong><span>{e(q['label'])}</span></figcaption>
</figure>"""
        for q in ctx.t["testimonials"]
    )
    return f"""<section class="section tint">
  <div class="wrap">
    <h2 class="section-title">{e(ctx.t['home']['testimonials_title'])}</h2>
    <div class="quotes">{cards}</div>
  </div>
</section>
"""


# ----------------------------------------------------------------- pages ---

def page_home(ctx):
    t, h = ctx.t, ctx.t["home"]
    badges = "".join(f"<li>{ico('check')}{e(b)}</li>" for b in h["badges"])
    svc_cards = "".join(
        f"""<article class="card">
  {ico(s['id'])}
  <h3>{e(s['title'])}</h3>
  <p>{e(s['short'])}</p>
  <a class="more" href="{ctx.url('services')}#{s['id']}">{e(t['common']['more'])}<span class="sr"> – {e(s['title'])}</span></a>
</article>"""
        for s in t["services"]["items"]
    )
    adv = "".join(
        f"""<li>{ico(ADV_ICONS[i])}<div><h3>{e(a['title'])}</h3><p>{e(a['text'])}</p></div></li>"""
        for i, a in enumerate(h["advantages"])
    )
    insurers = "".join(
        f'<li><a href="{e(i["url"])}" rel="noopener">{e(i["name"])}</a></li>' for i in load("en")["insurers"]
    )
    body = f"""
<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">{e(h['eyebrow'])}</p>
      <h1>{e(h['hero_title'])}</h1>
      <p class="lead">{e(h['hero_sub'])}</p>
      <div class="actions">
        <a class="btn" href="{ctx.url('contact')}">{e(h['cta_primary'])}</a>
        <a class="btn btn-ghost" href="{ctx.url('services')}">{e(h['cta_secondary'])}</a>
      </div>
      <ul class="badges">{badges}</ul>
    </div>
    <div class="hero-photo">
      <div class="arch">{photo(ctx, 'eager')}</div>
      <p class="chip">{ico('pin')}{e(t['common']['area'])}</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 class="section-title">{e(h['services_title'])}</h2>
    <p class="section-sub">{e(h['services_sub'])}</p>
    <div class="cards">{svc_cards}</div>
  </div>
</section>

<section class="section band-ink">
  <div class="wrap split">
    <div>
      <h2>{e(h['approach_title'])}</h2>
      <p>{e(h['approach_text'])}</p>
    </div>
    <div class="swirl" aria-hidden="true"><img src="{ctx.asset('img/icon-large.jpg')}" alt="" width="150"></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <h2 class="section-title">{e(h['why_title'])}</h2>
    <ul class="advantages">{adv}</ul>
  </div>
</section>

<section class="section tint">
  <div class="wrap meet">
    <div class="meet-photo">{photo(ctx, 'lazy')}</div>
    <div>
      <h2>{e(h['meet_title'])}</h2>
      <p>{e(h['meet_text'])}</p>
      <a class="btn btn-ghost" href="{ctx.url('about')}">{e(h['meet_cta'])}</a>
    </div>
  </div>
</section>

{testimonials(ctx)}

<section class="section">
  <div class="wrap two">
    <div>
      <h2>{e(h['area_title'])}</h2>
      <p>{e(h['area_text'])}</p>
    </div>
    <div>
      <h2>{e(h['insurers_title'])}</h2>
      <ul class="pills">{insurers}</ul>
    </div>
  </div>
</section>

{cta_band(ctx, h['final_title'], h['final_text'], h['final_cta'])}
"""
    return h["title"], h["description"], body


def page_services(ctx):
    s = ctx.t["services"]
    items = ""
    for it in s["items"]:
        pts = "".join(f"<li>{ico('check')}{e(p)}</li>" for p in it["points"])
        items += f"""<article class="service" id="{it['id']}">
  <div class="service-head">{ico(it['id'])}<h2>{e(it['title'])}</h2></div>
  <p>{e(it['body'])}</p>
  <ul class="ticks">{pts}</ul>
</article>"""
    steps = "".join(
        f"<li><span class=\"n\">{i}</span><div><h3>{e(x['title'])}</h3><p>{e(x['text'])}</p></div></li>"
        for i, x in enumerate(s["how"], 1)
    )
    body = f"""
<section class="page-head"><div class="wrap"><h1>{e(s['title'])}</h1><p class="lead">{e(s['intro'])}</p></div></section>
<section class="section"><div class="wrap narrow services">{items}</div></section>
<section class="section tint">
  <div class="wrap">
    <h2 class="section-title">{e(s['how_title'])}</h2>
    <ol class="steps">{steps}</ol>
  </div>
</section>
{cta_band(ctx, s['cta_title'], s['cta_text'], s['cta'])}
"""
    return s["title"], s["description"], body


def page_about(ctx):
    a = ctx.t["about"]
    quals = "".join(f"<li>{ico('check')}{e(q)}</li>" for q in a["quals"])
    blocks = "".join(
        f"<div class=\"card flat\"><h3>{e(a[k + '_title'])}</h3><p>{e(a[k])}</p></div>"
        for k in ["vision", "mission", "quality", "care"]
    )
    body = f"""
<section class="page-head"><div class="wrap"><h1>{e(a['title'])}</h1><p class="lead">{e(a['intro'])}</p></div></section>

<section class="section">
  <div class="wrap narrow"><h2>{e(a['philosophy_title'])}</h2><p class="big">{e(a['philosophy'])}</p></div>
</section>

<section class="section tint">
  <div class="wrap meet">
    <div class="meet-photo">{photo(ctx, 'lazy')}</div>
    <div>
      <h2>{e(a['mellany_title'])}</h2>
      <p class="role">{e(a['mellany_role'])}</p>
      <p>{e(a['mellany_intro'])}</p>
      <h3>{e(a['education_title'])}</h3><p>{e(a['education'])}</p>
      <h3>{e(a['registration_title'])}</h3><p>{e(a['registration'])}</p>
      <h3>{e(a['career_title'])}</h3><p>{e(a['career'])}</p>
      <h3>{e(a['quals_title'])}</h3><ul class="ticks">{quals}</ul>
      <h3>{e(a['languages_title'])}</h3><p>{e(a['languages'])}</p>
    </div>
  </div>
</section>

<section class="section"><div class="wrap"><div class="cards four">{blocks}</div></div></section>
{cta_band(ctx, ctx.t['home']['final_title'], ctx.t['home']['final_text'], a['cta'])}
"""
    return a["title"], a["description"], body


def page_faq(ctx):
    f = ctx.t["faq"]
    items = "".join(
        f"<details><summary>{e(i['q'])}</summary><p>{e(i['a'])}</p></details>" for i in f["items"]
    )
    body = f"""
<section class="page-head"><div class="wrap"><h1>{e(f['title'])}</h1></div></section>
<section class="section"><div class="wrap narrow faq">{items}</div></section>
{cta_band(ctx, ctx.t['services']['cta_title'], ctx.t['services']['cta_text'], ctx.t['services']['cta'])}
"""
    return f["title"], f["description"], body


def page_contact(ctx):
    c, com = ctx.t["contact"], ctx.t["common"]
    opts = "".join(f'<option value="{e(k)}">{e(v)}</option>' for k, v in c["service_options"].items())
    consent = e(c["consent"]).replace(
        "{privacy_link}", f'<a href="{ctx.url("privacy")}">{e(c["privacy_link_text"])}</a>'
    )
    msgs = json.dumps(
        {"sending": c["sending"], "submit": c["submit"], "error": c["error"], "invalid": c["invalid"], "not_configured": c["not_configured"]},
        ensure_ascii=False,
    )
    body = f"""
<section class="page-head"><div class="wrap"><h1>{e(c['title'])}</h1><p class="lead">{e(c['intro'])}</p></div></section>
<section class="section">
  <div class="wrap contact-grid">
    <aside class="details">
      <h2>{e(c['details_title'])}</h2>
      <ul class="plain icons">
        <li>{ico('pin')}<span><strong>{e(com['address_label'])}</strong><br>{e(com['address'])}</span></li>
        <li>{ico('phone')}<span><strong>{e(com['phone_label'])}</strong><br><a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a></span></li>
        <li>{ico('mail')}<span><strong>{e(com['email_label'])}</strong><br><a href="mailto:{EMAIL}">{EMAIL}</a></span></li>
        <li>{ico('clock')}<span><strong>{e(com['hours_label'])}</strong><br>{e(com['hours'])}<br>{e(com['closed'])}</span></li>
        <li>{ico('home')}<span>{e(com['area'])}</span></li>
      </ul>
    </aside>
    <div class="form-card">
      <h2>{e(c['form_title'])}</h2>
      <form id="contact-form" novalidate data-lang="{ctx.lang}" data-messages='{e(msgs, quote=True)}'>
        <div class="field"><label for="f-name">{e(c['name'])} <span class="req">*</span></label>
          <input id="f-name" name="name" type="text" autocomplete="name" required minlength="2" maxlength="120"></div>
        <div class="row">
          <div class="field"><label for="f-email">{e(c['email'])} <span class="req">*</span></label>
            <input id="f-email" name="email" type="email" autocomplete="email" required maxlength="254"></div>
          <div class="field"><label for="f-phone">{e(c['phone'])}</label>
            <input id="f-phone" name="phone" type="tel" autocomplete="tel" maxlength="40"></div>
        </div>
        <div class="row">
          <div class="field"><label for="f-town">{e(c['town'])}</label>
            <input id="f-town" name="town" type="text" maxlength="120" aria-describedby="town-hint">
            <small id="town-hint">{e(c['town_hint'])}</small></div>
          <div class="field"><label for="f-service">{e(c['service'])}</label>
            <select id="f-service" name="service">{opts}</select></div>
        </div>
        <div class="field"><label for="f-subject">{e(c['subject'])}</label>
          <input id="f-subject" name="subject" type="text" maxlength="200"></div>
        <div class="field"><label for="f-message">{e(c['message'])} <span class="req">*</span></label>
          <textarea id="f-message" name="message" rows="6" required minlength="5" maxlength="4000"></textarea></div>
        <fieldset class="field reply">
          <legend>{e(c['reply_by'])}</legend>
          <label><input type="radio" name="reply_by" value="email" checked> {e(c['reply_email'])}</label>
          <label><input type="radio" name="reply_by" value="phone"> {e(c['reply_phone'])}</label>
        </fieldset>
        <div class="hp" aria-hidden="true"><label>Website <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <label class="consent"><input type="checkbox" name="consent" required> <span>{consent} <span class="req">*</span></span></label>
        <p class="status" role="status" aria-live="polite"></p>
        <button class="btn" type="submit">{e(c['submit'])}</button>
      </form>
      <div class="success" hidden>
        <h3>{e(c['success_title'])}</h3><p>{e(c['success'])}</p>
      </div>
    </div>
  </div>
</section>
"""
    return c["title"], c["description"], body


def page_privacy(ctx):
    p = ctx.t["privacy"]
    secs = "".join(f"<h2>{e(s['h'])}</h2><p>{e(s['p'])}</p>" for s in p["sections"])
    body = f"""
<section class="page-head"><div class="wrap"><h1>{e(p['title'])}</h1></div></section>
<section class="section"><div class="wrap narrow prose"><p class="note">{e(p['draft'])}</p>{secs}</div></section>
"""
    return p["title"], p["description"], body


BUILDERS = {"home": page_home, "about": page_about, "services": page_services, "faq": page_faq, "contact": page_contact, "privacy": page_privacy}


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    base = load("en")
    translations = {l: load(l) for l in LANGS}
    for l in LANGS[1:]:
        missing = check_keys(base, translations[l])
        if missing:
            raise SystemExit(f"{l}.json is missing keys: {missing}")

    for l in LANGS:
        shutil.rmtree(SITE / l, ignore_errors=True)
    for lang in LANGS:
        t = translations[lang]
        for page in PAGES:
            ctx = Ctx(lang, page, t)
            title, desc, body = BUILDERS[page](ctx)
            write(SITE / lang / PATHS[page] / "index.html", head(ctx, title, desc) + header(ctx) + body + footer(ctx))

    # Root: pick a language from the browser, English is the fallback.
    write(SITE / "index.html", f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhysioFit365</title>
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="assets/img/favicon.ico" sizes="48x48">
<link rel="canonical" href="{BASE_URL}/en/">
<link rel="alternate" hreflang="x-default" href="{BASE_URL}/en/">
<noscript><meta http-equiv="refresh" content="0; url=en/"></noscript>
<script>
(function () {{
  var l = (navigator.language || "en").slice(0, 2).toLowerCase();
  location.replace(({json.dumps(LANGS)}.indexOf(l) > -1 ? l : "en") + "/");
}})();
</script></head>
<body><p><a href="en/">English</a> · <a href="nl/">Nederlands</a> · <a href="es/">Español</a></p></body></html>
""")
    urls = "".join(
        f"<url><loc>{abs_url(l, p)}</loc>" + "".join(
            f'<xhtml:link rel="alternate" hreflang="{x}" href="{abs_url(x, p)}"/>' for x in LANGS
        ) + "</url>\n"
        for l in LANGS for p in PAGES
    )
    write(SITE / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{urls}</urlset>\n')
    write(SITE / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print(f"Built {len(LANGS) * len(PAGES)} pages in {SITE}")


if __name__ == "__main__":
    main()

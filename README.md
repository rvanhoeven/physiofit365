# PhysioFit365

Website for PhysioFit365, home physiotherapy by Mellany van Hoeven in and around Rojales (Costa Blanca).
Languages: English (base), Nederlands, Español.

## Structure

- `content/en.json` (base), `nl.json`, `es.json` – all texts. The build fails if a translation misses a key.
- `build.py` – static generator, writes `site/<lang>/...` (home, about, services, faq, contact, privacy).
- `site/assets/` – css, js, logo and icons. **Add Mellany's photo as `site/assets/img/mellany.jpg`** (about 920x730 px or larger); until then a logo placeholder is shown.
- `supabase/migrations/` – database schema for the contact form (`contact_requests`).
- `site/assets/config.js` – Supabase URL and publishable (anon) key for the form.

## Build

    python3 build.py                                  # uses https://www.physiofit365.com for canonical links
    BASE_URL=https://example.com python3 build.py

## Database

`contact_requests` stores every form submission (name, email, phone, town, treatment type, subject, message,
preferred reply channel, page language, consent) plus internal follow-up fields (`status`, `handled_at`, `notes`).
Row Level Security lets the public site INSERT only; nobody can read through the public API.
Apply with the Supabase CLI or paste the migration into the SQL editor of a **dedicated** Supabase project,
then fill in `site/assets/config.js`.

## Branding

Colours come from the logo: magenta `#fa0dd6`, pink `#fe26ac`, coral `#fd866c`, orange `#e68e43`, ink `#17111b`.
The logo already carries the handwritten script, so the site uses a clean system font.
The Autography and Briliantine fonts supplied are personal-use-only licences and are intentionally NOT included;
a commercial licence from the designer is needed before using them on the site.

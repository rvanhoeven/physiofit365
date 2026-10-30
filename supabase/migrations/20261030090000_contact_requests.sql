-- PhysioFit365: contact requests sent through the website form.
-- Visitors (anon) may only INSERT. Nobody can read through the public API;
-- the practice reads requests in the Supabase dashboard (or via the service role).

create table if not exists public.contact_requests (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),

  -- what the visitor fills in
  name          text not null check (char_length(name) between 2 and 120),
  email         text not null check (char_length(email) between 5 and 254 and email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  phone         text check (phone is null or char_length(phone) between 6 and 40),
  town          text check (town is null or char_length(town) <= 120),
  service       text check (service is null or service in ('manual', 'work', 'sport', 'other')),
  subject       text check (subject is null or char_length(subject) <= 200),
  message       text not null check (char_length(message) between 5 and 4000),
  reply_by      text not null default 'email' check (reply_by in ('phone', 'email')),

  -- captured automatically by the form
  language      text not null default 'en' check (language in ('en', 'nl', 'es')),
  consent       boolean not null check (consent is true),
  consented_at  timestamptz not null default now(),

  -- internal follow-up by the practice (not writable by visitors)
  status        text not null default 'new' check (status in ('new', 'contacted', 'scheduled', 'closed')),
  handled_at    timestamptz,
  notes         text,

  -- a visitor who wants a phone answer must leave a phone number
  constraint phone_required_when_reply_by_phone check (reply_by <> 'phone' or phone is not null)
);

comment on table public.contact_requests is 'Messages and home-visit questions submitted through the PhysioFit365 website form.';
comment on column public.contact_requests.service is 'manual = manual therapy, work = work injury, sport = sport injury, other = something else / not sure';
comment on column public.contact_requests.language is 'Language of the website page the visitor used (en, nl, es).';

create index if not exists contact_requests_status_created_idx
  on public.contact_requests (status, created_at desc);

alter table public.contact_requests enable row level security;

-- Public website: insert only, and only a fresh, untouched request.
drop policy if exists "website can submit a request" on public.contact_requests;
create policy "website can submit a request"
  on public.contact_requests
  for insert
  to anon
  with check (status = 'new' and handled_at is null and notes is null and consent is true);

-- Column-level privileges: the website may only write the visitor fields.
revoke all on public.contact_requests from anon, authenticated;
grant insert (name, email, phone, town, service, subject, message, reply_by, language, consent)
  on public.contact_requests to anon;

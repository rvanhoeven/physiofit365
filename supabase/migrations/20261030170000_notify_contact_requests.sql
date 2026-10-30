-- Email notification for every new contact request.
-- A trigger calls the Edge Function "notify-contact-request" (through pg_net) with the id of the new row.
-- The function sends the mail with Resend and stamps notified_at, so nothing is mailed twice.

alter table public.contact_requests add column if not exists notified_at timestamptz;
comment on column public.contact_requests.notified_at is 'Set by the notify-contact-request function once the notification email was sent.';

create extension if not exists pg_net with schema extensions;

create or replace function public.notify_contact_request()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  perform net.http_post(
    url     := 'https://kmhsswngppprdaubpejb.supabase.co/functions/v1/notify-contact-request',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      -- public anon key: lets the call pass the function's JWT check; the function only acts on rows it finds itself
      'Authorization', 'Bearer sb_publishable_vjkGQTqsGr0JnuwGD54J3g_I4AhXJl2'
    ),
    body    := jsonb_build_object('id', new.id)
  );
  return new;
exception when others then
  -- never block a visitor's submission because the notification failed
  return new;
end;
$$;

revoke all on function public.notify_contact_request() from public, anon, authenticated;

drop trigger if exists contact_request_notify on public.contact_requests;
create trigger contact_request_notify
  after insert on public.contact_requests
  for each row execute function public.notify_contact_request();

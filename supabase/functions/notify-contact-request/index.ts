// Sends an email for every new row in public.contact_requests.
// Called by a database trigger (see supabase/migrations/20261030170000_notify_contact_requests.sql) with { id }.
// The function loads the row itself (service role) and only mails rows that have not been notified yet,
// so a stray call with an unknown or already-handled id sends nothing.
//
// Secrets (supabase secrets set ...):
//   RESEND_API_KEY   API key from resend.com
//   MAIL_FROM        e.g. "PhysioFit365 <formulier@physiofit365.com>"  (domain must be verified in Resend)
//   MAIL_TO          info@physiofit365.com
//   MAIL_BCC         rick@vanhoeven.es   (comma separated for more than one)
import { createClient } from "npm:@supabase/supabase-js@2";

const esc = (s: unknown) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
const list = (s: string | undefined) => (s ?? "").split(",").map((x) => x.trim()).filter(Boolean);

const SERVICE: Record<string, string> = {
  manual: "Manuele therapie", work: "Werkblessure", sport: "Sportblessure", other: "Anders / weet niet",
};
const LANG: Record<string, string> = { en: "Engels", nl: "Nederlands", es: "Spaans" };

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });

  let id: string | undefined;
  try { id = (await req.json())?.id; } catch { /* ignore */ }
  if (!id || !/^[0-9a-f-]{36}$/i.test(id)) return new Response("Bad request", { status: 400 });

  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data: r, error } = await db
    .from("contact_requests").select("*").eq("id", id).is("notified_at", null).maybeSingle();
  if (error) return new Response(error.message, { status: 500 });
  if (!r) return new Response("Nothing to send", { status: 200 });

  const to = list(Deno.env.get("MAIL_TO"));
  const bcc = list(Deno.env.get("MAIL_BCC"));
  const from = Deno.env.get("MAIL_FROM");
  const key = Deno.env.get("RESEND_API_KEY");
  if (!to.length || !from || !key) return new Response("Mail secrets are not configured", { status: 500 });

  const rows: [string, string][] = [
    ["Naam", r.name], ["E-mail", r.email], ["Telefoon", r.phone ?? "-"], ["Woonplaats / regio", r.town ?? "-"],
    ["Gaat over", SERVICE[r.service] ?? "-"], ["Onderwerp", r.subject ?? "-"],
    ["Antwoord graag per", r.reply_by === "phone" ? "Telefoon" : "E-mail"],
    ["Taal van de pagina", LANG[r.language] ?? r.language],
  ];
  const html = `<div style="font-family:system-ui,Arial,sans-serif;max-width:640px">
<h2 style="margin:0 0 12px">Nieuwe aanvraag via de website</h2>
<table style="border-collapse:collapse;width:100%">${rows.map(([k, v]) =>
    `<tr><td style="padding:6px 12px 6px 0;color:#666;vertical-align:top;white-space:nowrap">${esc(k)}</td><td style="padding:6px 0"><strong>${esc(v)}</strong></td></tr>`).join("")}</table>
<h3 style="margin:18px 0 6px">Bericht</h3>
<p style="white-space:pre-wrap;background:#fff2f9;border-radius:8px;padding:12px">${esc(r.message)}</p>
<p style="color:#888;font-size:12px">Ontvangen op ${esc(new Date(r.created_at).toLocaleString("nl-NL", { timeZone: "Europe/Madrid" }))}. Antwoord op deze mail gaat rechtstreeks naar de bezoeker.</p></div>`;
  const text = rows.map(([k, v]) => `${k}: ${v}`).join("\n") + `\n\nBericht:\n${r.message}\n`;

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from, to, bcc: bcc.length ? bcc : undefined, reply_to: r.email,
      subject: `Nieuwe aanvraag via website: ${String(r.name).slice(0, 80)}`, html, text,
    }),
  });
  if (!res.ok) return new Response(`Resend error ${res.status}: ${await res.text()}`, { status: 502 });

  await db.from("contact_requests").update({ notified_at: new Date().toISOString() }).eq("id", id);
  return new Response("Sent", { status: 200 });
});

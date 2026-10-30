(function () {
  "use strict";

  // Mobile navigation
  var btn = document.querySelector(".menu-btn");
  var nav = document.getElementById("nav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Contact form -> Supabase (insert-only through Row Level Security)
  var form = document.getElementById("contact-form");
  if (!form) return;

  var msgs = {};
  try { msgs = JSON.parse(form.getAttribute("data-messages") || "{}"); } catch (e) {}
  var status = form.querySelector(".status");
  var submit = form.querySelector('button[type="submit"]');
  var cfg = window.PHYSIOFIT_CONFIG || {};

  function setStatus(text, isError) {
    status.textContent = text || "";
    status.classList.toggle("error", !!isError);
  }

  function validate() {
    var ok = true;
    var firstBad = null;
    form.querySelectorAll(".field").forEach(function (f) { f.classList.remove("invalid"); });
    form.querySelectorAll("[required]").forEach(function (el) {
      if (!el.checkValidity()) {
        var f = el.closest(".field");
        if (f) f.classList.add("invalid");
        if (!firstBad) firstBad = el;
        ok = false;
      }
    });
    var replyBy = form.querySelector('input[name="reply_by"]:checked').value;
    var phone = form.elements.phone;
    if (replyBy === "phone" && !phone.value.trim()) {
      phone.closest(".field").classList.add("invalid");
      if (!firstBad) firstBad = phone;
      ok = false;
    }
    if (firstBad) firstBad.focus();
    return ok;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    setStatus("");
    if (form.elements.website.value) return;          // honeypot: bots fill this in
    if (!validate()) { setStatus(msgs.invalid, true); return; }
    if (!cfg.supabaseUrl || !cfg.supabaseAnonKey) { setStatus(msgs.not_configured, true); return; }

    var v = function (n) { var s = form.elements[n].value.trim(); return s ? s : null; };
    var row = {
      name: v("name"),
      email: v("email"),
      phone: v("phone"),
      town: v("town"),
      service: v("service"),
      subject: v("subject"),
      message: v("message"),
      reply_by: form.querySelector('input[name="reply_by"]:checked').value,
      language: form.getAttribute("data-lang") || "en",
      consent: form.elements.consent.checked
    };

    submit.disabled = true;
    submit.textContent = msgs.sending;

    fetch(cfg.supabaseUrl.replace(/\/$/, "") + "/rest/v1/contact_requests", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "apikey": cfg.supabaseAnonKey,
        "Authorization": "Bearer " + cfg.supabaseAnonKey,
        "Prefer": "return=minimal"
      },
      body: JSON.stringify(row)
    }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      form.hidden = true;
      form.parentNode.querySelector(".success").hidden = false;
    }).catch(function () {
      setStatus(msgs.error, true);
      submit.disabled = false;
      submit.textContent = msgs.submit;
    });
  });
})();

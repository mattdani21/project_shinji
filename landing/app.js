// Tessera landing — waitlist form injection from a single config file.
// Edit landing/waitlist.config.json to swap the destination (Google Form / Airtable).
(function () {
  "use strict";

  var cfg = null;
  var target = document.getElementById("waitlist-form");

  function renderPending(message) {
    target.innerHTML = '<p class="pending">' + message + "</p>";
  }

  function renderForm(formUrl) {
    // Google Form embed src; add sandbox-friendly attrs for a static site.
    var frame = document.createElement("iframe");
    frame.src = formUrl;
    frame.setAttribute("frameborder", "0");
    frame.setAttribute("marginheight", "0");
    frame.setAttribute("marginwidth", "0");
    target.innerHTML = "";
    target.appendChild(frame);
  }

  fetch("waitlist.config.json", { cache: "no-store" })
    .then(function (r) {
      if (!r.ok) throw new Error("config missing");
      return r.json();
    })
    .then(function (data) {
      cfg = data;
      if (cfg.form_url && cfg.form_url.length > 0) {
        renderForm(cfg.form_url);
      } else {
        renderPending("Waitlist opens soon.");
      }
    })
    .catch(function () {
      renderPending("Waitlist opens soon.");
    });
})();

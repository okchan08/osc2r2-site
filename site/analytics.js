/*
  Google Analytics, for every page under site/ — the playground included —
  and only for a visitor who has said yes.

  Loaded by a plain <script> in <head> — no async, no defer — so it has run
  before any module script does, and `window.gtag` exists by the time the
  playground's own code wants to report a run. The playground does not load
  Google's script itself: it calls `gtag` if it is there and does nothing if it
  is not, which is what keeps a local build of it out of the numbers. osc2r2's
  publish step writes the <script> tag for this file into site/app/index.html,
  and tools/check-links.py fails any page that does not carry it.

  Consent comes first. Until a visitor allows it, Google's script is not loaded,
  no cookie is set, and `gtag` drops what it is given rather than queueing it, so
  a run made before the choice is never sent after it. Every visitor is asked,
  wherever they are: the site has no server that could tell where a visitor is,
  and a free demo has no reason to count anybody who has not agreed. The choice
  is kept in localStorage under KEY, and privacy.html can change it; declining
  after allowing removes Analytics' cookies and reloads the page, which is the
  only way to unload a script.

  The one thing this must never do is send a fragment. A playground run writes
  the scenario, and sometimes a whole map, into the address bar after the `#`,
  and gtag would otherwise report the address as it finds it. So the page's
  location is set once, here, without one, and every event after that —
  including those sent after the fragment changes — carries this value rather
  than reading the address bar again. The query string is kept: it is where
  campaign tags (utm_*) arrive, and nothing on this site writes one.

  In the GA property, "Page changes based on browser history events" in
  enhanced measurement has to stay off. The playground replaces its history
  entry on every run, and that setting turns each one into a page_view.
*/
(function () {
  var MEASUREMENT_ID = "G-PQZ953P2WJ";
  var KEY = "osc2r2-analytics";

  // Where privacy.html is, from where this file was loaded: the playground and
  // the 404 page load it from other directories than the site's root.
  var self = document.currentScript && document.currentScript.src;
  var PRIVACY = self ? new URL("privacy.html", self).href : "privacy.html";

  function stored() {
    try {
      return window.localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function store(choice) {
    try {
      window.localStorage.setItem(KEY, choice);
    } catch (e) {
      // A browser that keeps nothing asks again on the next page, which is the
      // right way for that to fail.
    }
  }

  var choice = stored();
  var started = false;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    if (started) {
      window.dataLayer.push(arguments);
    }
  };

  function start() {
    if (started) {
      return;
    }
    started = true;
    // No advertising use of what is measured, whatever the property allows.
    gtag("consent", "default", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
    gtag("js", new Date());
    gtag("set", { page_location: location.origin + location.pathname + location.search });
    gtag("config", MEASUREMENT_ID);

    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
    document.head.appendChild(script);
  }

  // Analytics' own cookies: `_ga` and `_ga_<container>`, set on this host or
  // on the domain above it.
  function forget() {
    var host = location.hostname;
    document.cookie.split(";").forEach(function (cookie) {
      var name = cookie.split("=")[0].trim();
      if (name !== "_ga" && name.indexOf("_ga_") !== 0) {
        return;
      }
      ["", "; domain=" + host, "; domain=." + host].forEach(function (domain) {
        document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/" + domain;
      });
    });
  }

  function choose(next) {
    var was = choice;
    choice = next;
    store(next);
    var banner = document.getElementById("osc2r2-consent");
    if (banner) {
      banner.remove();
    }
    if (next === "granted") {
      start();
    } else if (was === "granted" || started) {
      forget();
      location.reload();
      return;
    }
    showStatus();
  }

  // privacy.html says what the choice is, next to the buttons that change it.
  function showStatus() {
    var said = {
      granted: "You have allowed Analytics on this site.",
      denied: "You have declined Analytics on this site.",
    };
    var text = said[choice] || "You have not chosen yet.";
    document.querySelectorAll("[data-consent-status]").forEach(function (element) {
      element.textContent = text;
    });
  }

  var STYLE =
    "#osc2r2-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:2147483000;" +
    "max-width:40em;margin:0 auto;padding:16px 18px;border-radius:12px;" +
    "background:#fff;color:#1c1a17;border:1px solid #cfc8bb;" +
    "box-shadow:0 8px 28px rgba(0,0,0,.18);" +
    "font:15px/1.55 ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif}" +
    "#osc2r2-consent p{margin:0 0 12px}" +
    "#osc2r2-consent a{color:#8f4205}" +
    "#osc2r2-consent .osc2r2-consent-actions{display:flex;gap:10px;flex-wrap:wrap}" +
    "#osc2r2-consent button{font:inherit;font-weight:560;padding:8px 18px;border-radius:9px;" +
    "cursor:pointer;background:#f2efea;color:#1c1a17;border:1px solid #cfc8bb}" +
    "#osc2r2-consent button:hover{background:#e2ddd4}" +
    "#osc2r2-consent button:focus-visible,#osc2r2-consent a:focus-visible{outline:2px solid #b45309;outline-offset:2px}" +
    "@media (prefers-color-scheme:dark){" +
    "#osc2r2-consent{background:#211f1c;color:#f0ece5;border-color:#45413b;box-shadow:0 8px 28px rgba(0,0,0,.5)}" +
    "#osc2r2-consent a{color:#f0a955}" +
    "#osc2r2-consent button{background:#1e1c1a;color:#f0ece5;border-color:#45413b}" +
    "#osc2r2-consent button:hover{background:#322f2b}}";

  // The two answers look the same and sit side by side: declining is as easy
  // as allowing.
  function ask() {
    var style = document.createElement("style");
    style.textContent = STYLE;
    document.head.appendChild(style);

    var banner = document.createElement("section");
    banner.id = "osc2r2-consent";
    banner.setAttribute("aria-label", "Analytics consent");

    var text = document.createElement("p");
    text.appendChild(
      document.createTextNode(
        "May this site count visits, and how the playground is used, with Google " +
          "Analytics? It sets cookies only if you allow it, and nothing you write " +
          "or open in the playground is ever sent. ",
      ),
    );
    var more = document.createElement("a");
    more.href = PRIVACY;
    more.textContent = "Privacy";
    text.appendChild(more);
    banner.appendChild(text);

    var actions = document.createElement("div");
    actions.className = "osc2r2-consent-actions";
    [
      ["granted", "Allow"],
      ["denied", "Decline"],
    ].forEach(function (answer) {
      var button = document.createElement("button");
      button.type = "button";
      button.setAttribute("data-consent", answer[0]);
      button.textContent = answer[1];
      actions.appendChild(button);
    });
    banner.appendChild(actions);
    document.body.appendChild(banner);
  }

  // One listener for the banner's buttons and privacy.html's alike.
  document.addEventListener("click", function (event) {
    var target = event.target;
    var button = target && target.closest ? target.closest("[data-consent]") : null;
    if (!button) {
      return;
    }
    var next = button.getAttribute("data-consent");
    if (next === "granted" || next === "denied") {
      choose(next);
    }
  });

  if (choice === "granted") {
    start();
  }

  function ready() {
    showStatus();
    if (choice !== "granted" && choice !== "denied") {
      ask();
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();

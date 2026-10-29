/*
  Google Analytics, for every page under site/ — the playground included.

  Loaded by a plain <script> in <head> — no async, no defer — so it has run
  before any module script does, and `window.gtag` exists by the time the
  playground's own code wants to report a run. The playground does not load Google's script itself: it calls
  `gtag` if it is there and does nothing if it is not, which is what keeps a
  local build of it out of the numbers. osc2r2's publish step writes the
  <script> tag for this file into site/app/index.html, and tools/check-links.py
  fails any page that does not carry it.

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

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    window.dataLayer.push(arguments);
  };

  gtag("js", new Date());
  gtag("set", { page_location: location.origin + location.pathname + location.search });
  gtag("config", MEASUREMENT_ID);

  var script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
  document.head.appendChild(script);
})();

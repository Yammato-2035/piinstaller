(function () {
  var key = "setuphelfer_consent_analytics";
  function getConsent() {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }
  function setConsent(value) {
    try {
      localStorage.setItem(key, value);
    } catch (e) {}
  }

  function showBanner() {
    var banner = document.getElementById("setuphelfer-consent");
    if (!banner) return;
    banner.hidden = false;
    banner.addEventListener("click", function (ev) {
      var target = ev.target;
      if (!target || !target.getAttribute) return;
      var decision = target.getAttribute("data-consent");
      if (!decision) return;
      setConsent(decision);
      banner.hidden = true;
      if (decision === "accept") {
        window.dispatchEvent(new CustomEvent("setuphelfer:consent-granted"));
      }
    });
  }

  function injectMatomo() {
    if (!window.setuphelferMatomo || !window.setuphelferMatomo.url || !window.setuphelferMatomo.siteId) {
      return;
    }
    window._paq = window._paq || [];
    window._paq.push(["trackPageView"]);
    window._paq.push(["enableLinkTracking"]);
    window._paq.push(["setTrackerUrl", window.setuphelferMatomo.url + "matomo.php"]);
    window._paq.push(["setSiteId", window.setuphelferMatomo.siteId]);
    window._paq.push(["setCookieConsentGiven"]);
    var d = document, g = d.createElement("script"), s = d.getElementsByTagName("script")[0];
    g.async = true;
    g.src = window.setuphelferMatomo.url + "matomo.js";
    s.parentNode.insertBefore(g, s);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var consent = getConsent();
    if (!consent) {
      showBanner();
      return;
    }
    if (consent === "accept") {
      injectMatomo();
    }
  });

  window.addEventListener("setuphelfer:consent-granted", injectMatomo);
})();

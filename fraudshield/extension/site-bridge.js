/**
 * Manee — runs only on the Manee website (see manifest). The page and the extension talk through window messages:
 *   page -> "ping"              extension answers "pong" (so the page knows the extension is installed)
 *   page -> "settings-changed"  the on/off switch was saved: re-read it now instead of waiting for the next check
 *   page -> "link" + token      link this browser to the signed-in account (no copy and paste), answer "link-result"
 * Only messages from this same page are accepted.
 */
(function () {
  "use strict";
  function reply(message) {
    window.postMessage(Object.assign({ source: "manee-ext" }, message), window.location.origin);
  }
  function ask(message, done) {
    try {
      chrome.runtime.sendMessage(message, function (response) {
        var failed = !!chrome.runtime.lastError; // the extension may be asleep or just reloaded
        done(failed ? null : response);
      });
    } catch (e) {
      done(null);
    }
  }

  window.addEventListener("message", function (event) {
    if (event.source !== window || event.origin !== window.location.origin) return;
    var data = event.data;
    if (!data || data.source !== "manee-site") return;

    if (data.type === "ping") {
      reply({ type: "pong" });
    } else if (data.type === "settings-changed") {
      ask({ type: "GET_ACCOUNT" }, function () {});
    } else if (data.type === "link" && typeof data.token === "string") {
      ask({ type: "LINK_ACCOUNT", token: data.token }, function (state) {
        reply({ type: "link-result", linked: !!(state && state.linked), error: (state && state.error) || null });
      });
    }
  });
})();

/**
 * Manee — hides every badge, card and banner while the website's switch is Inactive,
 * and shows them again when it is switched back on. Runs before the other content scripts.
 */
(function () {
  "use strict";
  var TOKEN_KEY = "fe:device-token";
  var ENABLED_KEY = "fe:enabled";

  function apply(data) {
    var linked = typeof data[TOKEN_KEY] === "string" && data[TOKEN_KEY] !== "";
    var off = linked && data[ENABLED_KEY] === false;
    if (off) document.documentElement.setAttribute("data-fe-off", "1");
    else document.documentElement.removeAttribute("data-fe-off");
  }

  try {
    chrome.storage.local.get([TOKEN_KEY, ENABLED_KEY], apply);
    chrome.storage.onChanged.addListener(function (changes, area) {
      if (area !== "local" || !(ENABLED_KEY in changes || TOKEN_KEY in changes)) return;
      chrome.storage.local.get([TOKEN_KEY, ENABLED_KEY], apply);
    });
  } catch (e) {
    // Not running as an extension page.
  }
})();

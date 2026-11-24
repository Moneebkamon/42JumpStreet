/**
 * Manee — the on/off switch shared by every part of the extension.
 * The website's Active / Inactive switch is stored by background.js (see syncConfig). Unlinked = always on.
 */

export const TOKEN_KEY = "fe:device-token";
export const ENABLED_KEY = "fe:enabled"; // last value of the on/off switch set on the website

export async function isEnabled() {
  try {
    const data = await chrome.storage.local.get([TOKEN_KEY, ENABLED_KEY]);
    if (typeof data[TOKEN_KEY] !== "string" || !data[TOKEN_KEY]) return true;
    return data[ENABLED_KEY] !== false;
  } catch {
    return true;
  }
}

/** Talks to the Manee browser extension through window messages (the extension's site-bridge.js answers). */

type Reply = { source: "manee-ext"; type: string; linked?: boolean; error?: string | null };

function send(message: Record<string, unknown>): void {
  window.postMessage({ source: "manee-site", ...message }, window.location.origin);
}

function waitFor(type: string, ms: number): Promise<Reply | null> {
  return new Promise((resolve) => {
    const done = (value: Reply | null) => {
      window.removeEventListener("message", onMessage);
      clearTimeout(timer);
      resolve(value);
    };
    const onMessage = (event: MessageEvent) => {
      const d = event.data as Reply | undefined;
      if (event.source === window && d && d.source === "manee-ext" && d.type === type) done(d);
    };
    const timer = setTimeout(() => done(null), ms);
    window.addEventListener("message", onMessage);
  });
}

/** True if the Manee extension is installed and has this page open to it. */
export async function extensionInstalled(): Promise<boolean> {
  const answer = waitFor("pong", 1200);
  send({ type: "ping" });
  return (await answer) !== null;
}

/** Hand a linking code to the extension. Resolves true once the extension says it is linked. */
export async function linkExtension(token: string): Promise<boolean> {
  const answer = waitFor("link-result", 6000);
  send({ type: "link", token });
  const r = await answer;
  return !!(r && r.linked);
}

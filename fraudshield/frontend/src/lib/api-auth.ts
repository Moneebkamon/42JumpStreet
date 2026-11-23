import { ApiError } from "./api-client";

export interface Me {
  username: string;
  role: "analyst" | "admin";
  auth_enabled?: boolean;
}

/** The signed-in user, or null when nobody is signed in. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  let res: Response;
  try {
    res = await fetch("/api/v1/auth/me", { cache: "no-store", signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the FraudShield service.");
  }
  if (res.status === 401) return null;
  if (!res.ok) throw new ApiError("The service returned an error.");
  return (await res.json()) as Me;
}

export async function login(username: string, password: string): Promise<Me> {
  let res: Response;
  try {
    res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    throw new ApiError("Could not reach the FraudShield service.");
  }
  if (res.status === 401) throw new ApiError("Wrong username or password.");
  if (res.status === 429) throw new ApiError("Too many sign-in attempts. Try again in a few minutes.");
  if (!res.ok) throw new ApiError("Could not sign in. Please try again.");
  return (await res.json()) as Me;
}

export async function logout(): Promise<void> {
  await fetch("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined);
}

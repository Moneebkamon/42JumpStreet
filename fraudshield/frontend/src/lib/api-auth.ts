import { ApiError } from "./api-client";

export type Role = "user" | "analyst" | "admin";

export interface Me {
  username: string;
  role: Role;
  email?: string | null;
  auth_enabled?: boolean;
}

export const isStaffRole = (role: Role | undefined): boolean => role === "analyst" || role === "admin";

/** The signed-in user, or null when nobody is signed in. */
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  let res: Response;
  try {
    res = await fetch("/api/v1/auth/me", { cache: "no-store", signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the Manee service.");
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
    throw new ApiError("Could not reach the Manee service.");
  }
  if (res.status === 401) throw new ApiError("Wrong username or password.");
  if (res.status === 429) throw new ApiError("Too many sign-in attempts. Try again in a few minutes.");
  if (!res.ok) throw new ApiError("Could not sign in. Please try again.");
  return (await res.json()) as Me;
}

export async function register(username: string, email: string, password: string): Promise<Me> {
  let res: Response;
  try {
    res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
  } catch {
    throw new ApiError("Could not reach the Manee service.");
  }
  if (res.status === 409) throw new ApiError("That username or email is already registered.");
  if (res.status === 429) throw new ApiError("Too many sign-ups from your connection. Try again later.");
  if (res.status === 422) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(typeof body?.detail === "string" ? body.detail : "Check your details: password needs 8+ characters.");
  }
  if (!res.ok) throw new ApiError("Could not create the account. Please try again.");
  return (await res.json()) as Me;
}

export async function changePassword(current: string, next: string): Promise<void> {
  const res = await fetch("/api/v1/auth/password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: current, new_password: next }),
  }).catch(() => null);
  if (!res) throw new ApiError("Could not reach the Manee service.");
  if (res.status === 403) throw new ApiError("Current password is wrong.");
  if (res.status === 422) throw new ApiError("The new password needs at least 8 characters.");
  if (!res.ok) throw new ApiError("Could not change the password.");
}

export async function logout(): Promise<void> {
  await fetch("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined);
}

import { afterEach, describe, expect, it, vi } from "vitest";

import { forgetRefresh, refreshTokens, resolveSession, setSessionCookies, ACCESS_COOKIE, REFRESH_COOKIE } from "./session";

function tokenResponse(access: string, refresh: string) {
  return new Response(JSON.stringify({ access, refresh }), { status: 200 });
}

describe("refreshTokens", () => {
  afterEach(() => {
    forgetRefresh("r1");
    forgetRefresh("r2");
  });

  it("shares one rotation between concurrent requests that carry the same old refresh token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(tokenResponse("a2", "r2"));

    const [first, second] = await Promise.all([refreshTokens("r1", fetchMock), refreshTokens("r1", fetchMock)]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(first).toEqual({ access: "a2", refresh: "r2" });
    expect(second).toEqual(first);
  });

  it("returns null when the backend rejects the refresh token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 401 }));
    await expect(refreshTokens("r1", fetchMock)).resolves.toBeNull();
  });

  it("lets a network failure reach the caller instead of logging the user out", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(refreshTokens("r1", fetchMock)).rejects.toThrow();
  });
});

describe("resolveSession", () => {
  afterEach(() => {
    forgetRefresh("r1");
  });

  it("uses the access cookie as it is when it is present", async () => {
    const session = await resolveSession((name) => (name === ACCESS_COOKIE ? "a1" : undefined));
    expect(session).toEqual({ access: "a1", rotated: null, loggedOut: false, hadRefresh: false });
  });

  it("reports a logged-out visitor when there are no cookies", async () => {
    const session = await resolveSession(() => undefined);
    expect(session.loggedOut).toBe(true);
    expect(session.access).toBeNull();
  });

  it("refreshes when only the refresh cookie is left", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(tokenResponse("a2", "r2")));
    const session = await resolveSession((name) => (name === REFRESH_COOKIE ? "r1" : undefined));
    expect(session.access).toBe("a2");
    expect(session.rotated).toEqual({ access: "a2", refresh: "r2" });
    vi.unstubAllGlobals();
  });
});

describe("setSessionCookies", () => {
  it("stores both tokens as httpOnly cookies", () => {
    const written: Array<[string, string, Record<string, unknown>]> = [];
    setSessionCookies(
      { set: (name, value, options) => written.push([name, value, options as Record<string, unknown>]) },
      { access: "a", refresh: "r" },
    );
    for (const [, , options] of written) expect(options.httpOnly).toBe(true);
    expect(written.map(([name]) => name)).toEqual([ACCESS_COOKIE, REFRESH_COOKIE]);
  });
});

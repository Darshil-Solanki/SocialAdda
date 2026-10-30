import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

afterEach(() => vi.unstubAllGlobals());

describe("POST /api/session/logout", () => {
  it("tells Django to revoke the refresh token as JSON, even when the browser sent no content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest("http://localhost:3000/api/session/logout/", {
      method: "POST",
      headers: { cookie: "sa_refresh=refresh-token-1" },
    });

    const response = await POST(request);

    expect(response.status).toBe(204);
    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("content-type")).toBe("application/json");
    expect(JSON.parse(init.body)).toEqual({ refresh: "refresh-token-1" });
    expect(response.headers.get("set-cookie")).toContain("sa_refresh=;");
  });
});

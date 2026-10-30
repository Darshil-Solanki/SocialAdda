import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./auth";

const api = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  loginSession: vi.fn(),
  registerSession: vi.fn(),
  endSession: vi.fn(async () => {}),
}));

vi.mock("./api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api")>()),
  apiFetch: api.apiFetch,
  loginSession: api.loginSession,
  registerSession: api.registerSession,
  endSession: api.endSession,
}));

const alpha = { id: 1, username: "alpha", email: "a@example.test", first_name: "Alpha", last_name: "A", bio: null, profile_pic: null, cover: null };
const beta = { id: 2, username: "beta", email: "b@example.test", first_name: "Beta", last_name: "B", bio: null, profile_pic: null, cover: null };

describe("AuthProvider account switching", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("a /me/ request that was already running cannot bring the previous user back after a login", async () => {
    // The first /me/ request (sent before the login) stays open until the test resolves it.
    let resolveStaleMe!: (user: unknown) => void;
    api.apiFetch.mockImplementation(
      () => new Promise((resolve) => { resolveStaleMe = resolve; }),
    );
    api.loginSession.mockResolvedValue({ user: beta });

    const client = new QueryClient();
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    );
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(api.apiFetch).toHaveBeenCalled());

    await act(() => result.current.login("beta", "password"));
    await waitFor(() => expect(result.current.user?.username).toBe("beta"));

    // The earlier response for the previous user arrives after the login.
    await act(async () => resolveStaleMe(alpha));
    await new Promise((done) => setTimeout(done, 50));
    expect(result.current.user?.username).toBe("beta");
  });
});

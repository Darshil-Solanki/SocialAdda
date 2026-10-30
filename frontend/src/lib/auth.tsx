"use client";

import { useQueryClient, type QueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";

import { endSession, loginSession, registerSession } from "./api";
import { useMe } from "./queries";
import type { CurrentUser } from "./types";

type RegisterInput = {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
};

type AuthContextValue = {
  user: CurrentUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

// Makes `user` the only account whose data is cached. Requests that were still running for the previous account
// (for example an earlier /me/) are cancelled first, so their late answers cannot put that account back.
async function switchAccount(queryClient: QueryClient, user: CurrentUser | null) {
  await queryClient.cancelQueries();
  queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== "me" });
  queryClient.setQueryData(["me"], user);
}

// The session itself lives in httpOnly cookies on the server. This provider only tracks the signed-in user.
export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const me = useMe(true);

  const login = useCallback(
    async (username: string, password: string) => {
      const result = await loginSession(username, password);
      await switchAccount(queryClient, result.user as CurrentUser);
    },
    [queryClient],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const result = await registerSession(input);
      await switchAccount(queryClient, result.user as CurrentUser);
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    // Revokes the refresh token on the server; the local state is cleared at once.
    void endSession();
    void switchAccount(queryClient, null);
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: me.data ?? null,
      loading: me.isPending,
      login,
      register,
      logout,
    }),
    [me.data, me.isPending, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

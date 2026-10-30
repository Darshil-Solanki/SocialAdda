"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useAuth } from "@/lib/auth";

import { LiveNotifications } from "./live-notifications";
import { Nav } from "./nav";
import { SuggestionsPanel } from "./suggestions";
import { Spinner } from "./ui";

// Layout shared by every signed-in page. The server layout already checked the session; this handles sign-out.
export function AppShell({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) return <Spinner label="Checking your session" />;

  return (
    <>
      <LiveNotifications />
      {/* Phones: one column with the navigation as a top bar. Tablets: navigation beside the feed.
          Desktops (xl and up): a third column for suggestions. content-start keeps rows from stretching. */}
      <div className="mx-auto grid max-w-6xl content-start grid-cols-1 gap-4 px-3 py-3 sm:px-4 md:grid-cols-[200px_minmax(0,1fr)] md:gap-6 xl:grid-cols-[200px_minmax(0,1fr)_280px]">
        <aside className="sticky top-0 z-30 -mx-3 bg-zinc-50/95 px-3 py-2 backdrop-blur sm:-mx-4 sm:px-4 dark:bg-zinc-950/95 md:top-4 md:mx-0 md:h-fit md:bg-transparent md:p-0 md:backdrop-blur-none dark:md:bg-transparent">
          <Nav />
        </aside>
        <main className="min-w-0 space-y-4">
          {/* Below xl the suggestions column is hidden, so offer the same list as a collapsible card. */}
          <details className="group rounded-2xl border border-zinc-200 bg-white xl:hidden dark:border-zinc-800 dark:bg-zinc-900">
            <summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold">
              Who to follow <span className="text-zinc-500 group-open:hidden">(show)</span>
            </summary>
            <div className="px-1 pb-1">
              <SuggestionsPanel bare />
            </div>
          </details>
          {children}
        </main>
        <aside className="hidden xl:block">
          <SuggestionsPanel />
        </aside>
      </div>
    </>
  );
}

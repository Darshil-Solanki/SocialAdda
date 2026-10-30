import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { makeQueryClient } from "@/lib/query-client";
import { SessionRequired, serverGet } from "@/lib/server/data";
import type { CurrentUser, OffsetPage, UserSummary } from "@/lib/types";

// Server layout: checks the session before anything renders and loads what the shell needs.
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  let user: CurrentUser;
  try {
    user = await serverGet<CurrentUser>("/me/");
  } catch (error) {
    if (error instanceof SessionRequired) redirect("/login");
    throw error;
  }

  const queryClient = makeQueryClient();
  queryClient.setQueryData(["me"], user);
  await queryClient.prefetchQuery({
    queryKey: ["suggestions"],
    queryFn: () => serverGet<OffsetPage<UserSummary>>("/users/suggestions/"),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <AppShell>{children}</AppShell>
    </HydrationBoundary>
  );
}

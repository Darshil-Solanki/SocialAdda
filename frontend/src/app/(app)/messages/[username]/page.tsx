import { dehydrate } from "@tanstack/react-query";
import { notFound } from "next/navigation";

import { Hydrate } from "@/components/hydrate";
import { makeQueryClient } from "@/lib/query-client";
import { NotFoundOnServer, prefetchCursor, serverGet } from "@/lib/server/data";
import type { UserProfile } from "@/lib/types";
import { ThreadView } from "@/views/thread-view";

export default async function ThreadPage({ params }: { params: Promise<{ username: string }> }) {
  const { username } = await params;
  const queryClient = makeQueryClient();
  try {
    const profile = await serverGet<UserProfile>(`/users/${encodeURIComponent(username)}/`);
    queryClient.setQueryData(["profile", username], profile);
  } catch (error) {
    if (error instanceof NotFoundOnServer) notFound();
    throw error;
  }
  await prefetchCursor(
    queryClient,
    ["messages", username],
    `/conversations/${encodeURIComponent(username)}/messages/`,
  );
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <ThreadView username={username} />
    </Hydrate>
  );
}

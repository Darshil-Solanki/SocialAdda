import { dehydrate } from "@tanstack/react-query";
import { notFound } from "next/navigation";

import { Hydrate } from "@/components/hydrate";
import { ProfileView } from "@/views/profile-view";
import { makeQueryClient } from "@/lib/query-client";
import { NotFoundOnServer, prefetchCursor, serverGet } from "@/lib/server/data";
import { postKeys } from "@/lib/keys";
import type { UserProfile } from "@/lib/types";

export default async function ProfilePage({ params }: { params: Promise<{ username: string }> }) {
  const { username } = await params;
  const queryClient = makeQueryClient();
  try {
    const profile = await serverGet<UserProfile>(`/users/${encodeURIComponent(username)}/`);
    queryClient.setQueryData(["profile", username], profile);
  } catch (error) {
    if (error instanceof NotFoundOnServer) notFound();
    throw error;
  }
  await prefetchCursor(queryClient, postKeys.author(username), `/posts/?author=${encodeURIComponent(username)}`);
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <ProfileView username={username} />
    </Hydrate>
  );
}

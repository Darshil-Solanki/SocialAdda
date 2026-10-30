import { dehydrate } from "@tanstack/react-query";

import { Hydrate } from "@/components/hydrate";
import { PostFeed } from "@/components/feed";
import { makeQueryClient } from "@/lib/query-client";
import { prefetchCursor } from "@/lib/server/data";
import { postKeys } from "@/lib/keys";

export default async function FollowingPage() {
  const queryClient = makeQueryClient();
  await prefetchCursor(queryClient, postKeys.following(), "/feed/following/");
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <PostFeed source="following" emptyText="Follow people to see their posts here." />
    </Hydrate>
  );
}

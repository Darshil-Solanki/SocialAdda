import { dehydrate } from "@tanstack/react-query";

import { Hydrate } from "@/components/hydrate";
import { PostFeed } from "@/components/feed";
import { makeQueryClient } from "@/lib/query-client";
import { prefetchCursor } from "@/lib/server/data";
import { postKeys } from "@/lib/keys";

export default async function SavedPage() {
  const queryClient = makeQueryClient();
  await prefetchCursor(queryClient, postKeys.saved(), "/saved/");
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <PostFeed source="saved" emptyText="Posts you bookmark show up here." />
    </Hydrate>
  );
}

import { dehydrate } from "@tanstack/react-query";

import { Hydrate } from "@/components/hydrate";
import { PostComposer } from "@/components/post-composer";
import { PostFeed } from "@/components/feed";
import { makeQueryClient } from "@/lib/query-client";
import { prefetchCursor } from "@/lib/server/data";
import { postKeys } from "@/lib/keys";

export default async function HomePage() {
  const queryClient = makeQueryClient();
  await prefetchCursor(queryClient, postKeys.feed(), "/posts/");
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <PostComposer />
      <PostFeed source="feed" emptyText="No posts yet. Write the first one!" />
    </Hydrate>
  );
}

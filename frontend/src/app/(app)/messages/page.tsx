import { dehydrate } from "@tanstack/react-query";

import { Hydrate } from "@/components/hydrate";
import { makeQueryClient } from "@/lib/query-client";
import { prefetchCursor } from "@/lib/server/data";
import { ConversationsView } from "@/views/conversations-view";

export default async function MessagesPage() {
  const queryClient = makeQueryClient();
  await prefetchCursor(queryClient, ["conversations"], "/conversations/");
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <ConversationsView />
    </Hydrate>
  );
}

import { dehydrate } from "@tanstack/react-query";

import { Hydrate } from "@/components/hydrate";
import { makeQueryClient } from "@/lib/query-client";
import { prefetchCursor } from "@/lib/server/data";
import { NotificationsView } from "@/views/notifications-view";

export default async function NotificationsPage() {
  const queryClient = makeQueryClient();
  await prefetchCursor(queryClient, ["notifications"], "/notifications/");
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <NotificationsView />
    </Hydrate>
  );
}

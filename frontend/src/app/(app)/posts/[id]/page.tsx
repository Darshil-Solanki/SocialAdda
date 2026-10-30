import { dehydrate } from "@tanstack/react-query";
import { notFound } from "next/navigation";

import { Hydrate } from "@/components/hydrate";
import { makeQueryClient } from "@/lib/query-client";
import { NotFoundOnServer, prefetchCursor, serverGet } from "@/lib/server/data";
import { postKeys } from "@/lib/keys";
import type { Post } from "@/lib/types";
import { PostView } from "@/views/post-view";

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^\d+$/.test(id)) notFound();
  const postId = Number(id);

  const queryClient = makeQueryClient();
  try {
    const post = await serverGet<Post>(`/posts/${postId}/`);
    queryClient.setQueryData(postKeys.detail(postId), post);
  } catch (error) {
    if (error instanceof NotFoundOnServer) notFound();
    throw error;
  }
  await prefetchCursor(queryClient, ["comments", postId], `/posts/${postId}/comments/`);
  return (
    <Hydrate state={dehydrate(queryClient)}>
      <PostView id={postId} />
    </Hydrate>
  );
}

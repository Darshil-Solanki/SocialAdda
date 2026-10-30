"use client";

import { flatten, usePostList } from "@/lib/queries";
import type { Post } from "@/lib/types";

import { PostCard } from "./post-card";
import { EmptyState, ErrorText, secondaryButtonClass, Spinner } from "./ui";
import { describeError } from "@/lib/api";

type Props = {
  source: "feed" | "following" | "saved" | { author: string };
  emptyText: string;
};

// Renders one cursor-paginated list of posts with a "load more" control.
export function PostFeed({ source, emptyText }: Props) {
  const posts = usePostList(source);
  const items: Post[] = flatten(posts.data);

  if (posts.isPending) return <Spinner label="Loading posts" />;
  if (posts.isError) return <ErrorText>{describeError(posts.error)}</ErrorText>;
  if (items.length === 0) return <EmptyState>{emptyText}</EmptyState>;

  return (
    <div className="space-y-4">
      {items.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
      {posts.hasNextPage && (
        <button
          className={`${secondaryButtonClass} w-full`}
          onClick={() => posts.fetchNextPage()}
          disabled={posts.isFetchingNextPage}
        >
          {posts.isFetchingNextPage ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}

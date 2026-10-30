"use client";

import Link from "next/link";

import { PostCard } from "@/components/post-card";
import { ErrorText, Spinner } from "@/components/ui";
import { describeError } from "@/lib/api";
import { usePost } from "@/lib/queries";

// A single post with its comments and replies open.
export function PostView({ id }: { id: number }) {
  const post = usePost(id);

  if (post.isPending) return <Spinner label="Loading post" />;
  if (post.isError) return <ErrorText>{describeError(post.error)}</ErrorText>;

  return (
    <>
      <Link href="/" className="text-sm text-sky-600 hover:underline">
        Back to home
      </Link>
      <PostCard post={post.data} startOpen />
    </>
  );
}

"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { describeError } from "@/lib/api";
import { flatten, useAddComment, useComments, useReplies } from "@/lib/queries";
import type { Comment } from "@/lib/types";

import { Avatar, ErrorText, buttonClass, formatTime, inputClass, secondaryButtonClass, Spinner } from "./ui";

// Top-level comments of a post. Each one can open its replies (one level deep, as the API allows).
export function Comments({ postId }: { postId: number }) {
  const comments = useComments(postId, true);
  const items: Comment[] = flatten(comments.data);

  return (
    <div className="mt-3 space-y-3 border-t border-zinc-200 pt-3 dark:border-zinc-800">
      <CommentForm postId={postId} placeholder="Write a comment" submitLabel="Comment" />

      {comments.isPending && <Spinner label="Loading comments" />}
      {comments.isError && <ErrorText>{describeError(comments.error)}</ErrorText>}
      <ul className="space-y-3">
        {items.map((comment) => (
          <CommentItem key={comment.id} postId={postId} comment={comment} />
        ))}
      </ul>
      {comments.hasNextPage && (
        <button
          className={secondaryButtonClass}
          onClick={() => comments.fetchNextPage()}
          disabled={comments.isFetchingNextPage}
        >
          Load more comments
        </button>
      )}
    </div>
  );
}

function CommentItem({ postId, comment }: { postId: number; comment: Comment }) {
  const [repliesOpen, setRepliesOpen] = useState(false);
  return (
    <li className="flex gap-3">
      <Avatar user={comment.author} size={32} />
      <div className="min-w-0 flex-1">
        <p className="text-sm">
          <Link href={`/u/${comment.author.username}`} className="font-semibold hover:underline">
            {comment.author.first_name || comment.author.username}
          </Link>{" "}
          <span className="whitespace-pre-wrap break-words">{comment.body}</span>
        </p>
        <div className="mt-1 flex gap-3 text-xs text-zinc-500">
          <time dateTime={comment.comment_time}>{formatTime(comment.comment_time)}</time>
          <button
            aria-expanded={repliesOpen}
            className="hover:underline"
            onClick={() => setRepliesOpen((open) => !open)}
          >
            {comment.reply_count > 0 ? `${repliesOpen ? "Hide" : "Show"} replies (${comment.reply_count})` : "Reply"}
          </button>
        </div>
        {repliesOpen && <Replies postId={postId} parentId={comment.id} />}
      </div>
    </li>
  );
}

function Replies({ postId, parentId }: { postId: number; parentId: number }) {
  const replies = useReplies(postId, parentId, true);
  const items: Comment[] = flatten(replies.data);
  return (
    <div className="mt-2 space-y-2 border-l-2 border-zinc-200 pl-3 dark:border-zinc-800">
      <CommentForm postId={postId} parentId={parentId} placeholder="Write a reply" submitLabel="Reply" />
      {replies.isPending && <Spinner label="Loading replies" />}
      {replies.isError && <ErrorText>{describeError(replies.error)}</ErrorText>}
      <ul className="space-y-2">
        {items.map((reply) => (
          <li key={reply.id} className="flex gap-2 text-sm">
            <Avatar user={reply.author} size={24} />
            <p className="min-w-0">
              <Link href={`/u/${reply.author.username}`} className="font-semibold hover:underline">
                {reply.author.first_name || reply.author.username}
              </Link>{" "}
              <span className="whitespace-pre-wrap break-words">{reply.body}</span>
            </p>
          </li>
        ))}
      </ul>
      {replies.hasNextPage && (
        <button
          className={secondaryButtonClass}
          onClick={() => replies.fetchNextPage()}
          disabled={replies.isFetchingNextPage}
        >
          Load more replies
        </button>
      )}
    </div>
  );
}

function CommentForm({
  postId,
  parentId,
  placeholder,
  submitLabel,
}: {
  postId: number;
  parentId?: number;
  placeholder: string;
  submitLabel: string;
}) {
  const [draft, setDraft] = useState("");
  const addComment = useAddComment(postId, parentId);

  function submit(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;
    addComment.mutate(body, { onSuccess: () => setDraft("") });
  }

  return (
    <form onSubmit={submit} className="flex gap-2">
      <input
        aria-label={placeholder}
        className={inputClass}
        maxLength={90}
        placeholder={placeholder}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <button className={buttonClass} disabled={addComment.isPending || !draft.trim()}>
        {submitLabel}
      </button>
      {addComment.isError && <div className="w-full"><ErrorText>{describeError(addComment.error)}</ErrorText></div>}
    </form>
  );
}

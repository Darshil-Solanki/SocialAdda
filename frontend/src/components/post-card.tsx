"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/lib/auth";
import { describeError } from "@/lib/api";
import { mediaUrl } from "@/lib/media";
import { useDeletePost, useToggleBookmark, useToggleLike, useUpdatePost, type PostEdit } from "@/lib/queries";
import type { Post } from "@/lib/types";

import { Comments } from "./comments";
import { Avatar, Card, ErrorText, buttonClass, formatTime, inputClass, secondaryButtonClass } from "./ui";

export function PostCard({ post, startOpen = false }: { post: Post; startOpen?: boolean }) {
  const { user } = useAuth();
  const [showComments, setShowComments] = useState(startOpen);
  const [editing, setEditing] = useState(false);
  const toggleLike = useToggleLike();
  const toggleBookmark = useToggleBookmark();
  const deletePost = useDeletePost();
  const isOwn = user?.id === post.author.id;
  const name = post.author.first_name || post.author.username;

  return (
    <Card className="p-4">
      <article aria-label={`Post by ${name}`}>
        <header className="flex items-start gap-3">
          <Link href={`/u/${post.author.username}`} aria-label={`Open ${name}'s profile`}>
            <Avatar user={post.author} />
          </Link>
          <div className="min-w-0 flex-1">
            <Link href={`/u/${post.author.username}`} className="font-semibold hover:underline">
              {name}
            </Link>{" "}
            <span className="text-sm text-zinc-500">@{post.author.username}</span>
            <Link href={`/posts/${post.id}/`} className="block text-xs text-zinc-500 hover:underline">
              <time dateTime={post.date_created}>{formatTime(post.date_created)}</time>
            </Link>
          </div>
          {isOwn && !editing && (
            <div className="flex gap-2 text-sm">
              <button className="text-sky-600 hover:underline" onClick={() => setEditing(true)}>
                Edit
              </button>
              <button
                className="text-red-600 hover:underline"
                onClick={() => {
                  if (window.confirm("Delete this post?")) deletePost.mutate(post.id);
                }}
              >
                Delete
              </button>
            </div>
          )}
        </header>

        {editing ? (
          <PostEditForm post={post} onDone={() => setEditing(false)} />
        ) : (
          <>
            {post.content_text && <p className="mt-3 whitespace-pre-wrap break-words">{post.content_text}</p>}
            {post.content_image && (
              // eslint-disable-next-line @next/next/no-img-element -- user uploads served by Django
              <img
                src={mediaUrl(post.content_thumbnail || post.content_image)}
                alt=""
                className="mt-3 max-h-[480px] w-full rounded-xl object-cover"
              />
            )}
          </>
        )}

        <footer className="mt-3 flex gap-5 text-sm text-zinc-600 dark:text-zinc-400">
          <button
            aria-pressed={post.is_liked}
            aria-label={post.is_liked ? "Unlike" : "Like"}
            className={post.is_liked ? "font-semibold text-rose-600" : "hover:text-rose-600"}
            onClick={() => toggleLike.mutate(post)}
          >
            ♥ {post.like_count}
          </button>
          <button
            aria-expanded={showComments}
            className="hover:text-sky-600"
            onClick={() => setShowComments((open) => !open)}
          >
            💬 {post.comment_count}
          </button>
          <button
            aria-pressed={post.is_saved}
            aria-label={post.is_saved ? "Remove bookmark" : "Bookmark"}
            className={post.is_saved ? "font-semibold text-emerald-600" : "hover:text-emerald-600"}
            onClick={() => toggleBookmark.mutate(post)}
          >
            {post.is_saved ? "Saved" : "Save"}
          </button>
        </footer>
        {(toggleLike.isError || toggleBookmark.isError || deletePost.isError) && (
          <ErrorText>
            {describeError(toggleLike.error ?? toggleBookmark.error ?? deletePost.error)}
          </ErrorText>
        )}
        {showComments && <Comments postId={post.id} />}
      </article>
    </Card>
  );
}

// Edit form: text, and the photo can be replaced or removed. Without a new photo or a removal, only the text is sent.
function PostEditForm({ post, onDone }: { post: Post; onDone: () => void }) {
  const updatePost = useUpdatePost();
  const [draft, setDraft] = useState(post.content_text);
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [removeImage, setRemoveImage] = useState(false);

  const hasText = draft.trim().length > 0;
  const hasImage = (Boolean(file) || (Boolean(post.content_image) && !removeImage));

  function saveEdit() {
    let body: PostEdit;
    if (file || removeImage) {
      const form = new FormData();
      form.append("content_text", draft.trim());
      if (file) form.append("content_image", file);
      if (removeImage && !file) form.append("remove_image", "true");
      body = form;
    } else {
      body = { content_text: draft.trim() };
    }
    updatePost.mutate({ id: post.id, body }, { onSuccess: onDone });
  }

  return (
    <div className="mt-3 space-y-2">
      <textarea
        aria-label="Edit post text"
        className={inputClass}
        maxLength={140}
        rows={3}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      {post.content_image && !file && (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={removeImage}
            onChange={(event) => setRemoveImage(event.target.checked)}
          />
          Remove the photo
        </label>
      )}
      <label className="block text-sm">
        <span className="mb-1 block">{post.content_image ? "Replace the photo" : "Add a photo"}</span>
        <input
          key={fileKey}
          type="file"
          accept="image/*"
          aria-label="Post photo"
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setRemoveImage(false);
          }}
        />
      </label>
      {!hasText && !hasImage && <ErrorText>A post needs text or a photo.</ErrorText>}
      {updatePost.isError && <ErrorText>{describeError(updatePost.error)}</ErrorText>}
      <div className="flex gap-2">
        <button
          className={buttonClass}
          onClick={saveEdit}
          disabled={updatePost.isPending || (!hasText && !hasImage)}
        >
          Save
        </button>
        <button
          className={secondaryButtonClass}
          onClick={() => {
            setFile(null);
            setFileKey((key) => key + 1);
            onDone();
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

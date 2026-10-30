"use client";

import Link from "next/link";

import { FollowButton } from "@/components/follow-button";
import { PostFeed } from "@/components/feed";
import {
  Avatar,
  DEFAULT_COVER,
  Card,
  ErrorText,
  Spinner,
  secondaryButtonClass,
} from "@/components/ui";
import { describeError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { mediaUrl } from "@/lib/media";
import { useProfile } from "@/lib/queries";

export function ProfileView({ username }: { username: string }) {
  const { user: me } = useAuth();
  const profile = useProfile(username);

  if (profile.isPending) return <Spinner label="Loading profile" />;
  if (profile.isError)
    return <ErrorText>{describeError(profile.error)}</ErrorText>;

  const data = profile.data;
  const isMe = me?.username === data.username;

  return (
    <>
      <Card className="overflow-hidden">
        <div className="h-40 overflow-hidden bg-zinc-300 dark:bg-zinc-700">
          {/* eslint-disable-next-line @next/next/no-img-element -- user uploads served by Django */}
          <img
            src={data.cover ? mediaUrl(data.cover) : DEFAULT_COVER}
            alt=""
            className="h-full w-full object-cover"
          />
        </div>
        <div className="p-6">
          <div className="-mt-16 flex flex-wrap items-end gap-4">
            <span className="rounded-full border-4 border-white dark:border-zinc-900">
              <Avatar user={data} size={80} />
            </span>
            <div className="min-w-0 flex-1">
              <h1 className="text-xl font-bold">
                {`${data.first_name} ${data.last_name}`.trim() || data.username}
              </h1>
              <p className="text-sm text-zinc-500">@{data.username}</p>
            </div>
            {isMe ? (
              <Link href="/settings" className={secondaryButtonClass}>
                Edit profile
              </Link>
            ) : (
              <FollowButton
                username={data.username}
                following={data.is_following}
              />
            )}
          </div>
          {data.bio && (
            <p className="mt-4 whitespace-pre-wrap text-sm">{data.bio}</p>
          )}
          <p className="mt-2 text-sm">
            <strong>{data.following_count}</strong> following ·{" "}
            <strong>{data.follower_count}</strong> followers
          </p>
          {!isMe && (
            <Link
              href={`/messages/${data.username}`}
              className="mt-4 inline-block text-sm text-sky-600 hover:underline"
            >
              Send a message
            </Link>
          )}
        </div>
      </Card>
      <PostFeed source={{ author: data.username }} emptyText="No posts yet." />
    </>
  );
}

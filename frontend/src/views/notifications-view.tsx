"use client";

import Link from "next/link";
import { useEffect } from "react";

import { Avatar, Card, EmptyState, ErrorText, Spinner, formatTime, secondaryButtonClass } from "@/components/ui";
import { describeError } from "@/lib/api";
import { flatten, useMarkNotificationsRead, useNotifications } from "@/lib/queries";
import type { Notification } from "@/lib/types";

const VERB_TEXT: Record<Notification["verb"], string> = {
  like: "liked your post",
  comment: "commented on your post",
  follow: "started following you",
};

export function NotificationsView() {
  const notifications = useNotifications();
  const markRead = useMarkNotificationsRead();
  const { mutate: markAllRead } = markRead;

  // Opening the page counts as reading it; run once per visit.
  useEffect(() => {
    markAllRead();
  }, [markAllRead]);

  if (notifications.isPending) return <Spinner label="Loading notifications" />;
  if (notifications.isError) return <ErrorText>{describeError(notifications.error)}</ErrorText>;

  const items: Notification[] = flatten(notifications.data);
  if (items.length === 0) return <EmptyState>No notifications yet.</EmptyState>;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-bold">Notifications</h1>
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.id}>
            <Card className={`flex items-center gap-3 p-4 ${item.read_at ? "" : "border-sky-400"}`}>
              <Link href={`/u/${item.actor.username}`}>
                <Avatar user={item.actor} />
              </Link>
              <p className="min-w-0 flex-1 text-sm">
                <Link href={`/u/${item.actor.username}`} className="font-semibold hover:underline">
                  {item.actor.first_name || item.actor.username}
                </Link>{" "}
                {item.post_id ? (
                  <Link href={`/posts/${item.post_id}/`} className="hover:underline">
                    {VERB_TEXT[item.verb]}
                  </Link>
                ) : (
                  VERB_TEXT[item.verb]
                )}
                <time className="block text-xs text-zinc-500" dateTime={item.created_at}>
                  {formatTime(item.created_at)}
                </time>
              </p>
            </Card>
          </li>
        ))}
      </ul>
      {notifications.hasNextPage && (
        <button
          className={`${secondaryButtonClass} w-full`}
          onClick={() => notifications.fetchNextPage()}
          disabled={notifications.isFetchingNextPage}
        >
          Load more
        </button>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";

import { Avatar, Card, EmptyState, ErrorText, Spinner } from "@/components/ui";
import { describeError } from "@/lib/api";
import { flatten, useConversations } from "@/lib/queries";
import type { Conversation } from "@/lib/types";

export function ConversationsView() {
  const conversations = useConversations();

  if (conversations.isPending) return <Spinner label="Loading conversations" />;
  if (conversations.isError) return <ErrorText>{describeError(conversations.error)}</ErrorText>;

  const items: Conversation[] = flatten(conversations.data).filter((item) => item.other_user);
  if (items.length === 0) {
    return <EmptyState>No conversations yet. Visit someone’s profile to send them a message.</EmptyState>;
  }

  return (
    <ul className="space-y-3">
      {items.map((conversation) => {
        const other = conversation.other_user!;
        return (
          <li key={conversation.id}>
            <Link href={`/messages/${other.username}`}>
              <Card className="flex items-center gap-3 p-4 hover:bg-zinc-100 dark:hover:bg-zinc-800">
                <Avatar user={other} />
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold">{other.first_name || other.username}</span>
                  <span className="block text-sm text-zinc-500">@{other.username}</span>
                </span>
                {conversation.unread_count > 0 && (
                  <span
                    aria-label={`${conversation.unread_count} unread`}
                    className="rounded-full bg-sky-600 px-2 py-0.5 text-xs font-semibold text-white"
                  >
                    {conversation.unread_count}
                  </span>
                )}
              </Card>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

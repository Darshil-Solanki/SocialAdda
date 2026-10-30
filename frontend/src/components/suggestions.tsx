"use client";

import Link from "next/link";

import { useSuggestions } from "@/lib/queries";

import { Avatar, Card, EmptyState, Spinner } from "./ui";
import { FollowButton } from "./follow-button";

export function SuggestionsPanel({ bare = false }: { bare?: boolean }) {
  const suggestions = useSuggestions();

  const Wrapper = bare ? "div" : Card;
  return (
    <Wrapper className="p-4">
      {!bare && <h2 className="mb-3 font-semibold">Who to follow</h2>}
      {suggestions.isPending && <Spinner />}
      {suggestions.data && suggestions.data.results.length === 0 && <EmptyState>No suggestions right now.</EmptyState>}
      <ul className="space-y-3">
        {suggestions.data?.results.map((user) => (
          <li key={user.id} className="flex items-center gap-3">
            <Link href={`/u/${user.username}`} className="flex min-w-0 flex-1 items-center gap-2">
              <Avatar user={user} size={36} />
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold">{user.first_name || user.username}</span>
                <span className="block truncate text-xs text-zinc-500">@{user.username}</span>
              </span>
            </Link>
            <FollowButton username={user.username} following={false} />
          </li>
        ))}
      </ul>
    </Wrapper>
  );
}

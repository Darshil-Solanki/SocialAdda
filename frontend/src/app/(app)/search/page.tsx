"use client";

import Link from "next/link";
import { useState } from "react";

import { FollowButton } from "@/components/follow-button";
import { Avatar, Card, EmptyState, ErrorText, inputClass, Spinner } from "@/components/ui";
import { describeError } from "@/lib/api";
import { useUserSearch } from "@/lib/queries";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const results = useUserSearch(query.trim());

  return (
    <>
      <Card className="p-4">
        <label htmlFor="people-search" className="mb-2 block text-sm font-semibold">
          Find people
        </label>
        <input
          id="people-search"
          type="search"
          className={inputClass}
          placeholder="Search by name or username"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </Card>

      {query.trim() === "" && <EmptyState>Type a name or username to search.</EmptyState>}
      {query.trim() !== "" && results.isPending && <Spinner label="Searching" />}
      {results.isError && <ErrorText>{describeError(results.error)}</ErrorText>}
      {results.data && results.data.results.length === 0 && <EmptyState>No one matches “{query.trim()}”.</EmptyState>}

      <ul className="space-y-3">
        {results.data?.results.map((user) => (
          <li key={user.id}>
            <Card className="flex items-center gap-3 p-4">
              <Link href={`/u/${user.username}`} className="flex min-w-0 flex-1 items-center gap-3">
                <Avatar user={user} />
                <span className="min-w-0">
                  <span className="block truncate font-semibold">{`${user.first_name} ${user.last_name}`.trim() || user.username}</span>
                  <span className="block truncate text-sm text-zinc-500">@{user.username}</span>
                </span>
              </Link>
              <FollowButton username={user.username} following={user.is_following} />
            </Card>
          </li>
        ))}
      </ul>
    </>
  );
}

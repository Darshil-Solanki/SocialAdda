"use client";

import { describeError } from "@/lib/api";
import { useFollow } from "@/lib/queries";

import { ErrorText, buttonClass, secondaryButtonClass } from "./ui";

export function FollowButton({ username, following }: { username: string; following: boolean }) {
  const follow = useFollow(username);
  return (
    <div>
      <button
        className={following ? secondaryButtonClass : buttonClass}
        disabled={follow.isPending}
        onClick={() => follow.mutate(!following)}
      >
        {following ? "Following" : "Follow"}
      </button>
      {follow.isError && <ErrorText>{describeError(follow.error)}</ErrorText>}
    </div>
  );
}

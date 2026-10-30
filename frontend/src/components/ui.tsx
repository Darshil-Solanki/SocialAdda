import type { ReactNode } from "react";

import type { UserSummary } from "@/lib/types";
import { mediaUrl } from "@/lib/media";

// Square size classes. Tailwind's preflight sets `img { height: auto }`, which overrides the height attribute, so
// without these classes a non-square photo is stretched into an oval.
const avatarSize: Record<number, string> = {
  24: "size-6",
  32: "size-8",
  36: "size-9",
  40: "size-10",
  64: "size-16",
  80: "size-20",
};

// Shipped in /public/defaults: used when a user has no photo (never set, or removed).
const DEFAULT_AVATAR = "/defaults/no_pic.png";
export const DEFAULT_COVER = "/defaults/no_covers.png";

export function Avatar({
  user,
  size = 40,
}: {
  user: UserSummary;
  size?: number;
}) {
  const sizeClass = avatarSize[size] ?? "size-10";
  return (
    // eslint-disable-next-line @next/next/no-img-element -- avatars come from the API host and need no optimizer
    <img
      src={user.profile_pic ? mediaUrl(user.profile_pic) : DEFAULT_AVATAR}
      alt=""
      width={size}
      height={size}
      className={`${sizeClass} shrink-0 rounded-full object-cover bg-zinc-200 dark:bg-zinc-700`}
    />
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div
      role="status"
      className="flex items-center justify-center p-6 text-sm text-zinc-500"
    >
      {label}…
    </div>
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  return (
    <p role="alert" className="text-sm text-red-600 dark:text-red-400">
      {children}
    </p>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="p-6 text-center text-sm text-zinc-500">{children}</p>;
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 ${className}`}
    >
      {children}
    </section>
  );
}

export const inputClass =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 dark:border-zinc-700 dark:bg-zinc-800";

export const buttonClass =
  "rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-50";

export const secondaryButtonClass =
  "rounded-full border border-zinc-300 px-4 py-2 text-sm font-semibold hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-800";

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

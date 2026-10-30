"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { Logo } from "./logo";
import { useAuth } from "@/lib/auth";
import { useUnreadCount } from "@/lib/queries";

const links = [
  { href: "/", label: "Home" },
  { href: "/notifications", label: "Notifications" },
  { href: "/following", label: "Following" },
  { href: "/saved", label: "Saved" },
  { href: "/search", label: "Search" },
  { href: "/messages", label: "Messages" },
  { href: "/settings", label: "Settings" },
];

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const unread = useUnreadCount(Boolean(user));
  const unreadCount = unread.data?.count ?? 0;

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <nav
      aria-label="Main"
      className="flex items-center gap-1 overflow-x-auto whitespace-nowrap [scrollbar-width:none] md:flex-col md:items-stretch md:overflow-visible [&::-webkit-scrollbar]:hidden"
    >
      <Link href="/" className="shrink-0 pr-2 md:px-3 md:pb-2 md:pt-2">
        <Logo className="h-7 md:h-9" />
      </Link>
      {links.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className={`shrink-0 rounded-full px-3 py-2 text-sm font-medium hover:bg-zinc-200 dark:hover:bg-zinc-800 ${
              active ? "bg-zinc-200 font-semibold dark:bg-zinc-800" : ""
            }`}
          >
            {link.label}
            {link.href === "/notifications" && unreadCount > 0 && (
              <span
                aria-label={`${unreadCount} unread notifications`}
                className="ml-1 rounded-full bg-rose-600 px-1.5 text-xs font-semibold text-white"
              >
                {unreadCount}
              </span>
            )}
          </Link>
        );
      })}
      {user && (
        <Link
          href={`/u/${user.username}`}
          className="shrink-0 rounded-full px-3 py-2 text-sm font-medium hover:bg-zinc-200 dark:hover:bg-zinc-800"
        >
          Profile
        </Link>
      )}
      <button
        onClick={handleLogout}
        className="shrink-0 rounded-full px-3 py-2 text-left text-sm font-medium text-red-600 hover:bg-zinc-200 dark:hover:bg-zinc-800"
      >
        Log out
      </button>
    </nav>
  );
}

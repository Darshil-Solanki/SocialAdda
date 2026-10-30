"use client";

import { useSyncExternalStore } from "react";

// Stored in a cookie (not localStorage) so the server can render the right theme on the first paint.
const COOKIE = "sa_theme";

function writeTheme(dark: boolean) {
  try {
    document.cookie = `${COOKIE}=${dark ? "dark" : "light"}; path=/; max-age=31536000; samesite=lax`;
  } catch {
    // Cookies blocked: the switch still works for this page view.
  }
}

// The theme is the "dark" class on <html>. Watching that class keeps this button correct however it changes.
function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

function isDark() {
  return document.documentElement.classList.contains("dark");
}

// Shown on every page. It flips the class on <html> at once and remembers the choice.
export function ThemeToggle() {
  // null on the server and during hydration, so the first render matches the server output.
  const dark = useSyncExternalStore<boolean | null>(subscribe, isDark, () => null);

  function toggle() {
    const next = !(dark ?? false);
    document.documentElement.classList.toggle("dark", next);
    writeTheme(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={dark ?? undefined}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="fixed right-3 bottom-3 z-50 flex size-11 items-center justify-center rounded-full border border-zinc-300 bg-white text-base shadow-md hover:bg-zinc-100 sm:size-auto sm:px-3 sm:py-2 sm:text-sm sm:font-medium dark:border-zinc-700 dark:bg-zinc-800 dark:hover:bg-zinc-700"
    >
      <span aria-hidden="true">{dark ? "☀" : "☾"}</span>
      <span className="hidden sm:ml-1 sm:inline">{dark === null ? "Theme" : dark ? "Light mode" : "Dark mode"}</span>
    </button>
  );
}

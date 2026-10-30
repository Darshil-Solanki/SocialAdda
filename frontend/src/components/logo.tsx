// Brand images from /public. "full" is the icon with the SocialAdda name; "icon" is the mark alone;
// "badge" is the mark in a round tile for the sign-in pages (transparent PNG, so it works in dark mode).
type Variant = "full" | "icon" | "badge";

export function Logo({ variant = "full", className = "" }: { variant?: Variant; className?: string }) {
  if (variant === "badge") {
    return (
      <span
        className={`mx-auto flex size-24 items-center justify-center rounded-full border border-sky-200 bg-sky-50 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 ${className}`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- static brand asset */}
        <img src="/logo_icon.png" alt="SocialAdda" width={500} height={500} className="size-16 object-contain" />
      </span>
    );
  }
  return variant === "full" ? (
    // eslint-disable-next-line @next/next/no-img-element -- static brand asset
    <img src="/logo.png" alt="SocialAdda" width={1920} height={380} className={`w-auto ${className}`} />
  ) : (
    // eslint-disable-next-line @next/next/no-img-element -- static brand asset
    <img src="/logo_icon.png" alt="SocialAdda" width={500} height={500} className={`w-auto ${className}`} />
  );
}

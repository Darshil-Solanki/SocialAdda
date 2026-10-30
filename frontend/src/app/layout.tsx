import type { Metadata } from "next";
import { cookies, headers } from "next/headers";
import { Geist, Geist_Mono } from "next/font/google";
import type { ReactNode } from "react";

import { Providers } from "@/components/providers";

import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SocialAdda",
  description: "Share posts, follow people and chat in real time.",
};

// Runs before the first paint when the visitor has not chosen a theme: it applies the device setting.
// The nonce lets it run under the Content-Security-Policy set by src/proxy.ts.
const SYSTEM_THEME_SCRIPT =
  "try{if(window.matchMedia('(prefers-color-scheme: dark)').matches)document.documentElement.classList.add('dark')}catch(e){}";

// Reading request headers and cookies makes every page render per request, so the proxy's CSP nonce reaches
// Next.js's scripts and the saved theme is in the first HTML the browser receives.
export default async function RootLayout({ children }: { children: ReactNode }) {
  const [requestHeaders, cookieStore] = await Promise.all([headers(), cookies()]);
  const nonce = requestHeaders.get("x-nonce") ?? undefined;
  const theme = cookieStore.get("sa_theme")?.value;
  const themeClass = theme === "dark" ? "dark" : "";

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${themeClass} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
        {!theme && <script nonce={nonce} dangerouslySetInnerHTML={{ __html: SYSTEM_THEME_SCRIPT }} />}
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

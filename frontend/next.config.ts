import type { NextConfig } from "next";

// Django serves uploaded media; the browser loads it from this origin. API calls go through the route handlers
// in src/app/api, which attach the session cookies. The Content-Security-Policy is set per request in src/proxy.ts.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Self-contained server output (node .next/standalone/server.js).
  output: "standalone",
  // Django routes end in slashes, so Next.js keeps them on every path.
  trailingSlash: true,
  async rewrites() {
    return [{ source: "/media/:path*", destination: `${BACKEND_URL}/media/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;

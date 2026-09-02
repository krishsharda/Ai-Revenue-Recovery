/** @type {import('next').NextConfig} */

// In development the Next server proxies /api to the local uvicorn backend, so
// the whole app is reachable on one URL (http://localhost:3000).
//
// In production this rewrite is deliberately absent: Vercel's top-level rewrite
// in vercel.json routes /api/* to the API service before the request ever
// reaches Next, and a competing rewrite here would shadow it.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN || "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (process.env.NODE_ENV === "production") return [];
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` }];
  },
};

module.exports = nextConfig;

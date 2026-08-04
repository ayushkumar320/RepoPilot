/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    const apiTarget = (process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    return [
      {
        // Everything under /api goes to the API *except* /api/auth/*, which
        // NextAuth's own route handler owns. The exclusion is load-bearing:
        // an array of rewrites is `afterFiles`, and afterFiles runs BEFORE
        // dynamic routes — so without it this proxy swallows the catch-all
        // /api/auth/[...nextauth] handler and OAuth callbacks 404 from FastAPI.
        source: "/api/:path((?!auth/).*)",
        destination: `${apiTarget}/:path`,
      },
    ];
  },
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiTarget = (process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${apiTarget}/:path*`,
      },
    ];
  },
};

export default nextConfig;

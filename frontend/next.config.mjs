/** @type {import('next').NextConfig} */
const nextConfig = {
  typedRoutes: false,
  async rewrites() {
    const apiProxyTarget = process.env.API_PROXY_TARGET;
    if (!apiProxyTarget) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`
      }
    ];
  }
};

export default nextConfig;

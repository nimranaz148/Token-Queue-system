import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/doctor-panel",
        destination: "/doctor",
        permanent: false,
      },
      {
        source: "/reception",
        destination: "/tokens",
        permanent: false,
      },
      {
        source: "/owner",
        destination: "/settings",
        permanent: false,
      },
      {
        source: "/admin",
        destination: "/admin/overview",
        permanent: false,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;

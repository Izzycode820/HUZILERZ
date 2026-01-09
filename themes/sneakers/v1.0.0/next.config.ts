import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow dev access from local network IPs
  allowedDevOrigins: ['192.168.*.*', '10.*.*.*', '172.16.*.*'],
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
    ],
  },
};

export default nextConfig;

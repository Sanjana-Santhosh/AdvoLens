import type { NextConfig } from "next";

// eslint-disable-next-line @typescript-eslint/no-require-imports
const withPWA = require("next-pwa")({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development", // Disable PWA in dev mode
});

const nextConfig: NextConfig = {
  // Use empty turbopack config for PWA webpack compatibility
  turbopack: {},
  // Allow local network access for mobile testing
  allowedDevOrigins: ["http://192.168.1.37:3000", "http://192.168.1.*:3000"],
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/uploads/**",
      },
    ],
  },
};

export default withPWA(nextConfig);

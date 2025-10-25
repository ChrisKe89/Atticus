/** @type {import('next').NextConfig} */
// Windows sandboxes cannot create symlinks reliably, so skip standalone output unless explicitly requested.
const useStandaloneOutput = process.platform !== "win32" || process.env.NEXT_STANDALONE === "1";

const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
  output: useStandaloneOutput ? "standalone" : undefined,
  eslint: {
    ignoreDuringBuilds: false,
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

module.exports = nextConfig;

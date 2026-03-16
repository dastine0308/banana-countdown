/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy /api calls to Flask backend in development
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:5000/:path*",
      },
    ];
  },
};

module.exports = nextConfig;

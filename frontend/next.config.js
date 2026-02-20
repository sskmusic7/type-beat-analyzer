/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // For Netlify, we can use standalone or export
  // Standalone works better with Netlify's Next.js plugin
}

module.exports = nextConfig

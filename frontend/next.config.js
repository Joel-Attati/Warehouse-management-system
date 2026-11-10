/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost', '127.0.0.1'],
    remotePatterns: [{ protocol: 'http', hostname: '**' }],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/uploads/:path*',
        destination: 'http://127.0.0.1:8000/static/uploads/:path*',
      },
    ]
  },
}

module.exports = nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export: FastAPI serves frontend/out at http://localhost:8000
  output: 'export',
  // Emit directory-style routes (nda-creator/index.html) so FastAPI's
  // StaticFiles(html=True) resolves them cleanly.
  trailingSlash: true,
  images: {
    // next/image needs a loader or optimization server; plain tags are fine for now
    unoptimized: true,
  },
}

module.exports = nextConfig

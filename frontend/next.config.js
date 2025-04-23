/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 기존 alias를 유지하면서 @ 별칭을 명시적으로 추가
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname), // '@'를 frontend 디렉토리의 절대 경로로 설정
    };

    // 기존 modules를 유지 (Next.js 기본값 + node_modules 등)
    // config.resolve.modules.push(path.resolve(__dirname, 'node_modules')); // 이 줄은 불필요할 수 있음

    return config;
  },
};

module.exports = nextConfig; 
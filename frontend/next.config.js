/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config) => {
    // tsconfig.json의 paths 설정을 webpack alias에 직접 매핑
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname), // '@'를 frontend 디렉토리의 절대 경로로 설정
    };
    // 중요: node_modules도 해석 경로에 포함되어야 함
    config.resolve.modules.push(path.resolve(__dirname, 'node_modules'));

    return config;
  },
};

module.exports = nextConfig; 
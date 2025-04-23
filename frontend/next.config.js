/** @type {import('next').NextConfig} */
const path = require('path');
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config) => {
    // 절대 경로 alias 설정
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    };
    // 모듈 해석 루트에 프로젝트 루트 추가
    config.resolve.modules = [
      path.resolve(__dirname),
      'node_modules',
      ...(config.resolve.modules || []),
    ];

    return config;
  },
};

module.exports = nextConfig; 
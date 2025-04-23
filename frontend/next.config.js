/** @type {import('next').NextConfig} */
// const path = require('path'); // path 모듈 불필요

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // webpack 설정 제거
  // webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
  //   config.resolve.alias = {
  //     ...config.resolve.alias,
  //     '@': path.resolve(__dirname),
  //   };
  //   return config;
  // },
};

module.exports = nextConfig; 
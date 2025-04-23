/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Log the existing alias configuration
    console.log("Existing Webpack resolve.alias:", config.resolve.alias);
    console.log("Existing Webpack resolve.modules:", config.resolve.modules);

    // Ensure tsconfig paths are respected (Next.js usually does this)
    // but let's see what the config looks like before potential modifications

    // If needed, explicitly add alias (redundant if tsconfig works, but for debugging)
    // config.resolve.alias['@'] = path.resolve(__dirname);
    // console.log("Set Webpack resolve.alias['@'] to:", path.resolve(__dirname));

    // Log final config before returning
    console.log("Final Webpack resolve.alias:", config.resolve.alias);
    console.log("Final Webpack resolve.modules:", config.resolve.modules);

    return config;
  },
};

module.exports = nextConfig; 
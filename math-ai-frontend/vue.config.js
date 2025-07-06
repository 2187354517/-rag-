const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true
})
// webpack.config.js
module.exports = {
  devServer: {
    allowedHosts: "all",
    client: {
      overlay: {
        // 添加这个配置过滤 Script error
        runtimeErrors: (error) => {
          if (error.message === 'Script error.') return false;
          return true;
        },
      }
    },
  },
};


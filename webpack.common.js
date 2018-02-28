const path = require("path");
const BundleTracker = require('webpack-bundle-tracker');

const DISTPATH = path.resolve(__dirname, 'assets/webpack_bundles');

module.exports = {
  mode: 'development',
  context: path.resolve(__dirname, 'assets/js'),
  entry: {
    listSearch: './listSearch.js',
  },
  plugins: [
    new BundleTracker({path: DISTPATH}),
  ],
  output: {
    filename: '[name]-[chunkhash].js',
    path: DISTPATH
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader?cacheDirectory=true',
          options: {
            presets: ['babel-preset-env', 'babel-preset-react']
          }
        }
      },
    ]
  }
};
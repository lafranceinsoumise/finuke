const path = require("path");
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const webpack = require('webpack');

const DISTPATH = path.resolve(__dirname, 'assets/webpack_bundles');

module.exports = {
  mode: 'development',
  devtool: 'inline-source-map',
  context: path.resolve(__dirname, 'assets/js'),
  entry: {
    publicListSearch: './publicListSearch',
    bureauListSearch: './bureauListSearch',
    formUtils: './formUtils'
  },
  plugins: [
    new CleanWebpackPlugin([DISTPATH]),
    new BundleTracker({path: DISTPATH}),
    new webpack.DefinePlugin({
        'BASE_URL': JSON.stringify(process.env.BASE_URL || '')
    })
  ],
  resolve: {
    alias: {
      CSVData: path.resolve(__dirname, 'votes/data')
    }
  },
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
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.csv$/,
        loader: 'csv-loader',
        options: {
          dynamicTyping: true,
          header: true,
          skipEmptyLines: true
        }
      }
    ]
  }
};

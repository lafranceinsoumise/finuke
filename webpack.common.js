const path = require("path");
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const webpack = require('webpack');

const DISTPATH = path.resolve(__dirname, 'assets/webpack_bundles');
const __VERSION__ = Math.random().toString(36).substring(2, 10);

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
        'BASE_URL': JSON.stringify(process.env.BASE_URL || ''),
        'DEPARTEMENT_PRESELECT': process.env.DEPARTEMENT_PRESELECT || false,
        'ELECTRONIC_VOTE_REQUIRE_BIRTHDATE': (process.env.ELECTRONIC_VOTE_REQUIRE_BIRTHDATE || "false").toLowerCase() === 'true',
        'ELECTRONIC_VOTE_REQUIRE_LIST': (process.env.ELECTRONIC_VOTE_REQUIRE_LIST || "false").toLowerCase() === 'true',
        'PHYSICAL_VOTE_REQUIRE_LIST': (process.env.PHYSICAL_VOTE_REQUIRE_LIST || process.env.ELECTRONIC_VOTE_REQUIRE_LIST || "false").toLowerCase() === 'true',
        'COMMUNES': JSON.stringify(!!process.env.COMMUNES && process.env.COMMUNES.split(',')),
        'DEPARTEMENTS': JSON.stringify(!!process.env.DEPARTEMENTS && process.env.DEPARTEMENTS.split(',')),
        'ENABLE_VOTING': (process.env.ENABLE_VOTING || 'true').toLowerCase() === 'true',
        'ENABLE_HIDING_VOTERS': (process.env.ENABLE_HIDING_VOTERS || 'true').toLowerCase() === 'true',
        '__VERSION__': JSON.stringify(__VERSION__)
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

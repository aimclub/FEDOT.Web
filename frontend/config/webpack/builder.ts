import { Configuration } from "webpack";
import { IOptions } from "./types";
import { resolvers } from "./resolvers";
import { buildLoaders } from "./loaders";
import { buildDevServer } from "./devServer";
import { buildPlugins } from "./plugins";
import { optimization } from "./optimization";

export const buildWebpackConfig = (options: IOptions): Configuration => ({
  mode: options.mode,
  entry: options.paths.entry,
  output: {
    path: options.paths.build,
    filename: "[name].[contenthash].js",
    chunkFilename: "[name].chunk.js",
    publicPath: "/",
    clean: options.isDev,
  },
  resolve: resolvers,
  module: { rules: buildLoaders(options) },
  plugins: buildPlugins(options),
  devtool: options.isDev ? "cheap-module-source-map" : "source-map",
  devServer: options.isDev ? buildDevServer(options) : undefined,
  optimization: options.isDev ? { runtimeChunk: "single" } : optimization,
});

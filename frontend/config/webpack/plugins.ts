import { CleanWebpackPlugin } from "clean-webpack-plugin";
import Dotenv from "dotenv-webpack";
import ESLintPlugin from "eslint-webpack-plugin";
import HTMLWebpackPlugin from "html-webpack-plugin";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import webpack, { WebpackPluginInstance } from "webpack";
import { BundleAnalyzerPlugin } from "webpack-bundle-analyzer";
import { IOptions } from "./types";

export const buildPlugins = ({
  paths,
  isDev,
  isBundleAnalyzer,
}: IOptions): WebpackPluginInstance[] => {
  const plugins: WebpackPluginInstance[] = [
    new CleanWebpackPlugin(),
    new webpack.ProgressPlugin(),
    new Dotenv({ path: paths.env }),
    new HTMLWebpackPlugin({
      template: paths.html,
    }),
    new MiniCssExtractPlugin({
      filename: "css/[name].[contenthash:8].css",
      chunkFilename: "css/[name].[contenthash:8].css",
    }),
  ];

  if (isDev) {
    plugins.push(
      new ESLintPlugin({
        extensions: ["js", "jsx", "ts", "tsx"],
      })
    );
  }

  if (isBundleAnalyzer) {
    plugins.push(new BundleAnalyzerPlugin());
  }

  return plugins;
};

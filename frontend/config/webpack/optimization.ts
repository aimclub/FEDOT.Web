import { Configuration } from "webpack";
import TerserWebpackPlugin from "terser-webpack-plugin";

export const optimization: Configuration["optimization"] = {
  minimizer: [new TerserWebpackPlugin()],
  splitChunks: {
    chunks: "all",
  },
};

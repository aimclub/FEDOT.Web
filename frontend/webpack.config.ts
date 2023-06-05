import path from "path";
import webpack from "webpack";
import { IBuildEnv } from "./config/webpack/types";
import { buildWebpackConfig } from "./config/webpack/builder";

const resolvePath = (...args: string[]) => path.resolve(__dirname, ...args);

export default ({
  mode = "development",
  port = 3001,
  isBundleAnalyzer = false,
}: IBuildEnv): webpack.Configuration =>
  buildWebpackConfig({
    mode,
    port,
    isDev: mode === "development",
    isBundleAnalyzer,
    paths: {
      entry: resolvePath("src", "index.tsx"),
      build: resolvePath("build"),
      html: resolvePath("public", "index.html"),
      favicon: resolvePath("public", "favicon.ico"),
      src: resolvePath("src"),
      env: resolvePath(`.env`),
    },
  });

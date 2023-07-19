import type { Configuration as DevServerConfiguration } from "webpack-dev-server";
import { IOptions } from "./types";

export const buildDevServer = (options: IOptions): DevServerConfiguration => ({
  port: options.port,
  open: true,
  hot: true,
  compress: true,
  historyApiFallback: true,
});

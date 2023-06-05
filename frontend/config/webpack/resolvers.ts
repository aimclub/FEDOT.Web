import { ResolveOptions } from "webpack";

export const resolvers: ResolveOptions = {
  extensions: [".js", ".jsx", ".ts", ".tsx", ".css", ".scss"],
  modules: ["node_modules"],
  mainFiles: ["index"],
};

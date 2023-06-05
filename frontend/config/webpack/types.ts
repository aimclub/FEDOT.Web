export type BuildMode = "development" | "production";

export interface IBuildPaths {
  entry: string;
  build: string;
  html: string;
  src: string;
  favicon: string;
  env: string;
}

export interface IBuildEnv {
  mode?: BuildMode;
  port?: number;
  isBundleAnalyzer?: boolean;
}

export interface IOptions extends Required<IBuildEnv> {
  isDev: boolean;
  paths: IBuildPaths;
}

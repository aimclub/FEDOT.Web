declare namespace SandboxEpochModuleScssNamespace {
  export interface ISandboxEpochModuleScss {
    content: string;
    icon: string;
    root: string;
    title: string;
  }
}

declare const SandboxEpochModuleScssModule: SandboxEpochModuleScssNamespace.ISandboxEpochModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxEpochModuleScssNamespace.ISandboxEpochModuleScss;
};

export = SandboxEpochModuleScssModule;

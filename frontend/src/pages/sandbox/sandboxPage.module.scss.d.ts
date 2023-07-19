declare namespace SandboxPageModuleScssNamespace {
  export interface ISandboxPageModuleScss {
    root: string;
  }
}

declare const SandboxPageModuleScssModule: SandboxPageModuleScssNamespace.ISandboxPageModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPageModuleScssNamespace.ISandboxPageModuleScss;
};

export = SandboxPageModuleScssModule;

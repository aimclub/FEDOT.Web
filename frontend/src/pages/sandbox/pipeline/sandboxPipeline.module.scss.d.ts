declare namespace SandboxPipelineModuleScssNamespace {
  export interface ISandboxPipelineModuleScss {
    graph: string;
    root: string;
  }
}

declare const SandboxPipelineModuleScssModule: SandboxPipelineModuleScssNamespace.ISandboxPipelineModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineModuleScssNamespace.ISandboxPipelineModuleScss;
};

export = SandboxPipelineModuleScssModule;

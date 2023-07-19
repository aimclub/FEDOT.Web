declare namespace SandboxPipelineNodeParamsModuleScssNamespace {
  export interface ISandboxPipelineNodeParamsModuleScss {
    close: string;
    header: string;
    root: string;
    title: string;
  }
}

declare const SandboxPipelineNodeParamsModuleScssModule: SandboxPipelineNodeParamsModuleScssNamespace.ISandboxPipelineNodeParamsModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineNodeParamsModuleScssNamespace.ISandboxPipelineNodeParamsModuleScss;
};

export = SandboxPipelineNodeParamsModuleScssModule;

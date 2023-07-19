declare namespace SandboxPipelineNodeEdgesModuleScssNamespace {
  export interface ISandboxPipelineNodeEdgesModuleScss {
    close: string;
    header: string;
    root: string;
    title: string;
  }
}

declare const SandboxPipelineNodeEdgesModuleScssModule: SandboxPipelineNodeEdgesModuleScssNamespace.ISandboxPipelineNodeEdgesModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineNodeEdgesModuleScssNamespace.ISandboxPipelineNodeEdgesModuleScss;
};

export = SandboxPipelineNodeEdgesModuleScssModule;

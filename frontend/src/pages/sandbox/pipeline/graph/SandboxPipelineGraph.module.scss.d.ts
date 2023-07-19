declare namespace SandboxPipelineGraphModuleScssNamespace {
  export interface ISandboxPipelineGraphModuleScss {
    bubbleNode: string;
    empty: string;
    root: string;
  }
}

declare const SandboxPipelineGraphModuleScssModule: SandboxPipelineGraphModuleScssNamespace.ISandboxPipelineGraphModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineGraphModuleScssNamespace.ISandboxPipelineGraphModuleScss;
};

export = SandboxPipelineGraphModuleScssModule;

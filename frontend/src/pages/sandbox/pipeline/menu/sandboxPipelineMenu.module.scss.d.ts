declare namespace SandboxPipelineMenuModuleScssNamespace {
  export interface ISandboxPipelineMenuModuleScss {
    item: string;
    menu: string;
    root: string;
    title: string;
    visible: string;
  }
}

declare const SandboxPipelineMenuModuleScssModule: SandboxPipelineMenuModuleScssNamespace.ISandboxPipelineMenuModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineMenuModuleScssNamespace.ISandboxPipelineMenuModuleScss;
};

export = SandboxPipelineMenuModuleScssModule;

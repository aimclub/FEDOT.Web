declare namespace SandboxPipelineButtonsModuleScssNamespace {
  export interface ISandboxPipelineButtonsModuleScss {
    button: string;
    icon: string;
    root: string;
  }
}

declare const SandboxPipelineButtonsModuleScssModule: SandboxPipelineButtonsModuleScssNamespace.ISandboxPipelineButtonsModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxPipelineButtonsModuleScssNamespace.ISandboxPipelineButtonsModuleScss;
};

export = SandboxPipelineButtonsModuleScssModule;

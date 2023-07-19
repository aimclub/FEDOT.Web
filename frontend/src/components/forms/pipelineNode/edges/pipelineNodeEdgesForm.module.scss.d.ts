declare namespace PipelineNodeEdgesFormModuleScssNamespace {
  export interface IPipelineNodeEdgesFormModuleScss {
    bottom: string;
    button: string;
    cancel: string;
    error: string;
    item: string;
    root: string;
    submit: string;
    text: string;
  }
}

declare const PipelineNodeEdgesFormModuleScssModule: PipelineNodeEdgesFormModuleScssNamespace.IPipelineNodeEdgesFormModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: PipelineNodeEdgesFormModuleScssNamespace.IPipelineNodeEdgesFormModuleScss;
};

export = PipelineNodeEdgesFormModuleScssModule;

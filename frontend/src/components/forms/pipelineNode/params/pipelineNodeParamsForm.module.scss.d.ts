declare namespace PipelineNodeParamsFormModuleScssNamespace {
  export interface IPipelineNodeParamsFormModuleScss {
    add: string;
    bottom: string;
    button: string;
    cancel: string;
    error: string;
    field: string;
    head: string;
    icon: string;
    null: string;
    params: string;
    ratting: string;
    root: string;
    row: string;
    submit: string;
    text: string;
    top: string;
  }
}

declare const PipelineNodeParamsFormModuleScssModule: PipelineNodeParamsFormModuleScssNamespace.IPipelineNodeParamsFormModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: PipelineNodeParamsFormModuleScssNamespace.IPipelineNodeParamsFormModuleScss;
};

export = PipelineNodeParamsFormModuleScssModule;

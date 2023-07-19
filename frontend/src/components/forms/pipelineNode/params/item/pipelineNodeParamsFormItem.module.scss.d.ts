declare namespace PipelineNodeParamsFormItemModuleScssNamespace {
  export interface IPipelineNodeParamsFormItemModuleScss {
    icon: string;
    root: string;
  }
}

declare const PipelineNodeParamsFormItemModuleScssModule: PipelineNodeParamsFormItemModuleScssNamespace.IPipelineNodeParamsFormItemModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: PipelineNodeParamsFormItemModuleScssNamespace.IPipelineNodeParamsFormItemModuleScss;
};

export = PipelineNodeParamsFormItemModuleScssModule;

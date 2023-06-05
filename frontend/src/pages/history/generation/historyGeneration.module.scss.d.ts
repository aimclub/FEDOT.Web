declare namespace HistoryGenerationModuleScssNamespace {
  export interface IHistoryGenerationModuleScss {
    active: string;
    content: string;
    root: string;
    tab: string;
    tabs: string;
  }
}

declare const HistoryGenerationModuleScssModule: HistoryGenerationModuleScssNamespace.IHistoryGenerationModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HistoryGenerationModuleScssNamespace.IHistoryGenerationModuleScss;
};

export = HistoryGenerationModuleScssModule;

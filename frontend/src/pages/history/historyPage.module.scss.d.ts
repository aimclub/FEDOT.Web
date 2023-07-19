declare namespace HistoryPageModuleScssNamespace {
  export interface IHistoryPageModuleScss {
    root: string;
  }
}

declare const HistoryPageModuleScssModule: HistoryPageModuleScssNamespace.IHistoryPageModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HistoryPageModuleScssNamespace.IHistoryPageModuleScss;
};

export = HistoryPageModuleScssModule;

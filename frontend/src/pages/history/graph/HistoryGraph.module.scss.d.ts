declare namespace HistoryGraphModuleScssNamespace {
  export interface IHistoryGraphModuleScss {
    button: string;
    center: string;
    empty: string;
    graph: string;
    root: string;
    tools: string;
  }
}

declare const HistoryGraphModuleScssModule: HistoryGraphModuleScssNamespace.IHistoryGraphModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HistoryGraphModuleScssNamespace.IHistoryGraphModuleScss;
};

export = HistoryGraphModuleScssModule;

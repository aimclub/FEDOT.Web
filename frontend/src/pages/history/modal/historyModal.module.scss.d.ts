declare namespace HistoryModalModuleScssNamespace {
  export interface IHistoryModalModuleScss {
    bottom: string;
    button: string;
    cancel: string;
    content: string;
    cose: string;
    empty: string;
    header: string;
    image: string;
    submit: string;
    title: string;
  }
}

declare const HistoryModalModuleScssModule: HistoryModalModuleScssNamespace.IHistoryModalModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HistoryModalModuleScssNamespace.IHistoryModalModuleScss;
};

export = HistoryModalModuleScssModule;

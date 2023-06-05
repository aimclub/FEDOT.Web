declare namespace ShowcaseInfoDetailsModuleScssNamespace {
  export interface IShowcaseInfoDetailsModuleScss {
    item: string;
    metric: string;
    root: string;
    value: string;
  }
}

declare const ShowcaseInfoDetailsModuleScssModule: ShowcaseInfoDetailsModuleScssNamespace.IShowcaseInfoDetailsModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: ShowcaseInfoDetailsModuleScssNamespace.IShowcaseInfoDetailsModuleScss;
};

export = ShowcaseInfoDetailsModuleScssModule;

declare namespace ShowcasePageModuleScssNamespace {
  export interface IShowcasePageModuleScss {
    root: string;
  }
}

declare const ShowcasePageModuleScssModule: ShowcasePageModuleScssNamespace.IShowcasePageModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: ShowcasePageModuleScssNamespace.IShowcasePageModuleScss;
};

export = ShowcasePageModuleScssModule;

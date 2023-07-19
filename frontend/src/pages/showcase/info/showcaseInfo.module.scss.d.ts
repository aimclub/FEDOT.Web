declare namespace ShowcaseInfoModuleScssNamespace {
  export interface IShowcaseInfoModuleScss {
    bottom: string;
    description: string;
    hidden: string;
    image: string;
    info: string;
    link: string;
    paper: string;
    root: string;
    subTitle: string;
    title: string;
  }
}

declare const ShowcaseInfoModuleScssModule: ShowcaseInfoModuleScssNamespace.IShowcaseInfoModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: ShowcaseInfoModuleScssNamespace.IShowcaseInfoModuleScss;
};

export = ShowcaseInfoModuleScssModule;

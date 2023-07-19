declare namespace HeaderBreadcrumbsModuleScssNamespace {
  export interface IHeaderBreadcrumbsModuleScss {
    icon: string;
    link: string;
    root: string;
    text: string;
  }
}

declare const HeaderBreadcrumbsModuleScssModule: HeaderBreadcrumbsModuleScssNamespace.IHeaderBreadcrumbsModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HeaderBreadcrumbsModuleScssNamespace.IHeaderBreadcrumbsModuleScss;
};

export = HeaderBreadcrumbsModuleScssModule;

declare namespace HeaderModuleScssNamespace {
  export interface IHeaderModuleScss {
    container: string;
    icon: string;
    line: string;
    root: string;
    text: string;
    title: string;
  }
}

declare const HeaderModuleScssModule: HeaderModuleScssNamespace.IHeaderModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HeaderModuleScssNamespace.IHeaderModuleScss;
};

export = HeaderModuleScssModule;

declare namespace HeaderMenuModuleScssNamespace {
  export interface IHeaderMenuModuleScss {
    button: string;
    icon: string;
    menu: string;
    menuItem: string;
    menuLabel: string;
    menuPaper: string;
    root: string;
  }
}

declare const HeaderMenuModuleScssModule: HeaderMenuModuleScssNamespace.IHeaderMenuModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: HeaderMenuModuleScssNamespace.IHeaderMenuModuleScss;
};

export = HeaderMenuModuleScssModule;

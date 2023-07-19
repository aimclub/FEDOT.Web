declare namespace LeftMenuModuleScssNamespace {
  export interface ILeftMenuModuleScss {
    active: string;
    disabled: string;
    head: string;
    icon: string;
    link: string;
    list: string;
    logo: string;
    menu: string;
    root: string;
    title: string;
  }
}

declare const LeftMenuModuleScssModule: LeftMenuModuleScssNamespace.ILeftMenuModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: LeftMenuModuleScssNamespace.ILeftMenuModuleScss;
};

export = LeftMenuModuleScssModule;

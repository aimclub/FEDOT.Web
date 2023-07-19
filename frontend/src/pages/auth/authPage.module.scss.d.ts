declare namespace AuthPageModuleScssNamespace {
  export interface IAuthPageModuleScss {
    foot: string;
    footItem: string;
    loader: string;
    logo: string;
    paper: string;
    root: string;
    title: string;
  }
}

declare const AuthPageModuleScssModule: AuthPageModuleScssNamespace.IAuthPageModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: AuthPageModuleScssNamespace.IAuthPageModuleScss;
};

export = AuthPageModuleScssModule;

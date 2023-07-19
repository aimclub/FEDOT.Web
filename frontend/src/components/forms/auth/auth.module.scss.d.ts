declare namespace AuthModuleScssNamespace {
  export interface IAuthModuleScss {
    error: string;
    root: string;
  }
}

declare const AuthModuleScssModule: AuthModuleScssNamespace.IAuthModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: AuthModuleScssNamespace.IAuthModuleScss;
};

export = AuthModuleScssModule;

declare namespace AppLoaderModuleScssNamespace {
  export interface IAppLoaderModuleScss {
    blackout: string;
  }
}

declare const AppLoaderModuleScssModule: AppLoaderModuleScssNamespace.IAppLoaderModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: AppLoaderModuleScssNamespace.IAppLoaderModuleScss;
};

export = AppLoaderModuleScssModule;

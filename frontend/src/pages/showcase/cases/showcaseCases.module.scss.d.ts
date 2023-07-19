declare namespace ShowcaseCasesModuleScssNamespace {
  export interface IShowcaseCasesModuleScss {
    cases: string;
    root: string;
    title: string;
  }
}

declare const ShowcaseCasesModuleScssModule: ShowcaseCasesModuleScssNamespace.IShowcaseCasesModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: ShowcaseCasesModuleScssNamespace.IShowcaseCasesModuleScss;
};

export = ShowcaseCasesModuleScssModule;

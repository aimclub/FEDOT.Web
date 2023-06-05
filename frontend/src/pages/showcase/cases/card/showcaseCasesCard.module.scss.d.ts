declare namespace ShowcaseCasesCardModuleScssNamespace {
  export interface IShowcaseCasesCardModuleScss {
    button: string;
    caption: string;
    image: string;
    root: string;
    title: string;
  }
}

declare const ShowcaseCasesCardModuleScssModule: ShowcaseCasesCardModuleScssNamespace.IShowcaseCasesCardModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: ShowcaseCasesCardModuleScssNamespace.IShowcaseCasesCardModuleScss;
};

export = ShowcaseCasesCardModuleScssModule;

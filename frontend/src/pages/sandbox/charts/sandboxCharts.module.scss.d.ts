declare namespace SandboxChartsModuleScssNamespace {
  export interface ISandboxChartsModuleScss {
    axis: string;
    chart: string;
    content: string;
    link: string;
    mark: string;
    null: string;
    paper: string;
    root: string;
    subtitle: string;
    top: string;
  }
}

declare const SandboxChartsModuleScssModule: SandboxChartsModuleScssNamespace.ISandboxChartsModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: SandboxChartsModuleScssNamespace.ISandboxChartsModuleScss;
};

export = SandboxChartsModuleScssModule;

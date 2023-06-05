declare namespace WorkSpaceModuleScssNamespace {
  export interface IWorkSpaceModuleScss {
    content: string;
    header: string;
    leftMenu: string;
    root: string;
  }
}

declare const WorkSpaceModuleScssModule: WorkSpaceModuleScssNamespace.IWorkSpaceModuleScss & {
  /** WARNING: Only available when `css-loader` is used without `style-loader` or `mini-css-extract-plugin` */
  locals: WorkSpaceModuleScssNamespace.IWorkSpaceModuleScss;
};

export = WorkSpaceModuleScssModule;

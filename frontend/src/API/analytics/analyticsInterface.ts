export type GenerationType = "pheno" | "geno";

export interface IGeneration {
  series: IGenerationSeries[];
}

export interface IGenerationSeries {
  y:
    | Int8Array
    | Uint8Array
    | Int16Array
    | Uint16Array
    | Int32Array
    | Uint32Array
    | Uint8ClampedArray
    | Float32Array
    | Float64Array;
  x: number[];
  type: "box";
  name: number | string;
}

export interface IMetric {
  options: {
    chart: {
      type: string;
    };
    xaxis: {
      categories: number[];
      title: {
        text: string;
      };
    };
    yaxis: {
      title: {
        text: string;
      };
      min: number;
      max: number;
    };
  };
  series: {
    name: string;
    data: number[];
  }[];
}

export interface IResult<
  ChartType extends "line" | "scatter" = "line" | "scatter"
> {
  options: {
    chart: {
      type: ChartType;
    };
    xaxis: {
      categories: number[];
      title: { text: string };
    };
    yaxis: {
      min: number;
      max: number;
      title: { text: string };
    };
  };
  series: {
    name: string;
    data: number[];
  }[];
}

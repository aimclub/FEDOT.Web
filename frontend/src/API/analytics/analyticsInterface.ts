export type GenerationType = "pheno" | "geno";

export interface IGeneration {
  series: IGenerationSeries[];
}

export interface IGenerationSeries {
  y: number;
  x: number[];
  type: string;
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

export interface IResult {
  options: {
    chart: {
      type: "line" | "scatter";
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

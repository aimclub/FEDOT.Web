export interface ICaseItem {
  case_id: string;
  description: string;
  icon_path: string;
  individual_id: string;
  title: string;
}

export interface ICase {
  case_id: string;
  description: string;
  icon_path: string;
  individual_id: string;
  title: string;
  details: Record<string, number>;
  // {
  //   n_features: number;
  //   n_levels: number;
  //   n_models: number;
  //   n_rows: number;
  //   [key: string]: number;
  // };
}

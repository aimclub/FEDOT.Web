export interface ICaseItem {
  case_id: string;
  description: string;
  icon_path: string;
  pipeline_id: string;
  title: string;
}

export interface ICase {
  case_id: string;
  description: string;
  icon_path: string;
  pipeline_id: string;
  title: string;
  details: {
    n_features: number;
    n_levels: number;
    n_models: number;
    n_rows: number;
    [key: string]: number;
  };
}

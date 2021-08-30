export interface ICaseArr {
  description: string;
  case_id: string;
  icon_path: string;
  pipeline_id: string;
  title: string;
}

export interface ICase {
  description: string;
  case_id: string;
  icon_path: string;
  pipeline_id: string;
  title: string;
  details: {
    f1: number;
    n_features: number;
    n_levels: number;
    n_models: number;
    n_rows: number;
    roc_auc: number;
  };
}

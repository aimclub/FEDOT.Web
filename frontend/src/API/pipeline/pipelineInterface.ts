export interface IEdgeData {
  source: number;
  target: number;
}

export interface INodeData {
  children: number[];
  display_name: string;
  id: number;
  model_name: string;
  params: NodeDataParamsType;
  parents: number[];
  rating?: number;
  type: NodeDataType;
}

export type NodeDataType = "model" | "data_operation";

export type NodeDataParamsType =
  | { [key: string]: string | number | boolean }
  | "default_params";

export interface IPipeline {
  edges: IEdgeData[];
  nodes: INodeData[];
  uid: string;
}

export interface IPipelineImage {
  image_url: string;
  uid: string;
}

export interface IValidate {
  error_desc: string;
  is_valid: boolean;
}
export interface IAdd extends IPipeline {
  is_new?: boolean;
}

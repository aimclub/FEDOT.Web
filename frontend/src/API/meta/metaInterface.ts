import { NodeDataType } from "../pipeline/pipelineInterface";

export interface IMetricName {
  display_name: string;
  metric_name: string;
}

export interface IModelName {
  display_name: string;
  model_name: string;
  type: NodeDataType;
}

export interface ITask {
  display_name: string;
  task_name: string;
}

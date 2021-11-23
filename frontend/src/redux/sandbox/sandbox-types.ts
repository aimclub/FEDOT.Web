import { ThunkAction } from "redux-thunk";
import { IMetric, IResult } from "../../API/analytics/analyticsInterface";
import { IModelName } from "../../API/meta/metaInterface";
import { ICaseParams, IEpoch } from "../../API/sanbox/sandboxInterface";
import { StateType } from "../store";
import { initialState } from "./sandbox-reducer";

export enum SandboxActionsEnum {
  SET_CASE_PARAMS = "SET_CASE_PARAMS",
  SET_EPOCHS = "SET_EPOCHS",
  SET_EPOCHS_LOADING = "SET_EPOCHS_LOADING",
  SET_EPOCH_SELECTED = "SET_EPOCH_SELECTED",
  SET_METRIC = "SET_METRIC",
  SET_METRIC_LOADING = "SET_METRIC_LOADING",
  SET_MODEL_NAMES = "SET_MODEL_NAMES",
  SET_RESULT = "SET_RESULT",
  SET_RESULT_LOADING = "SET_RESULT_LOADING",
}

export type PipelineFromType = "showcase" | "epoch" | "history" | "evaluate";

export type InitialStateType = typeof initialState;

export type ThunkTypeAsync = ThunkAction<
  Promise<void>,
  StateType,
  unknown,
  AllTypes
>;

// export type ThunkType = ThunkAction<void, StateType, unknown, AllTypes>;

export type AllTypes =
  | SetCaseParams
  | SetEpochs
  | SetEpochsLoading
  | SetEpochSelected
  | SetMetric
  | SetMetricLoading
  | SetModelNames
  | SetResult
  | SetResultLoading;

export type SetCaseParams = {
  type: SandboxActionsEnum.SET_CASE_PARAMS;
  data: ICaseParams;
};

export type SetEpochs = {
  type: SandboxActionsEnum.SET_EPOCHS;
  data: IEpoch[];
};

export type SetEpochsLoading = {
  type: SandboxActionsEnum.SET_EPOCHS_LOADING;
  data: boolean;
};

export type SetEpochSelected = {
  type: SandboxActionsEnum.SET_EPOCH_SELECTED;
  data: IEpoch;
};

export type SetMetric = {
  type: SandboxActionsEnum.SET_METRIC;
  data: IMetric | null;
};

export type SetMetricLoading = {
  type: SandboxActionsEnum.SET_METRIC_LOADING;
  data: boolean;
};

export type SetModelNames = {
  type: SandboxActionsEnum.SET_MODEL_NAMES;
  data: IModelName[];
};

export type SetResult = {
  type: SandboxActionsEnum.SET_RESULT;
  data: IResult | null;
};

export type SetResultLoading = {
  type: SandboxActionsEnum.SET_RESULT_LOADING;
  data: boolean;
};

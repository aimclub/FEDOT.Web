import { IMetric, IResult } from "../../API/analytics/analyticsInterface";
import { ICaseParams, IEpoch } from "../../API/sanbox/sandboxInterface";
import {
  AllTypes,
  InitialStateType,
  PipelineFromType,
  SandboxActionsEnum,
} from "./sandbox-types";

export const initialState = {
  caseParams: {} as ICaseParams,
  epochs: [] as IEpoch[],
  epochSelected: {} as IEpoch,
  isLoadingEpochs: false,
  isLoadingMetric: false,
  isLoadingResult: false,
  metric: null as IMetric | null,
  pipelineUid: null as string | null,
  pipelineFrom: null as PipelineFromType | null,
  result: null as IResult | null,
};

const sandboxReducer = (
  state = initialState,
  action: AllTypes
): InitialStateType => {
  switch (action.type) {
    case SandboxActionsEnum.SET_CASE_PARAMS:
      return { ...state, caseParams: action.data };

    case SandboxActionsEnum.SET_EPOCHS:
      return { ...state, epochs: action.data };

    case SandboxActionsEnum.SET_EPOCHS_LOADING:
      return { ...state, isLoadingEpochs: action.data };

    case SandboxActionsEnum.SET_EPOCH_SELECTED:
      return { ...state, epochSelected: action.data };

    case SandboxActionsEnum.SET_METRIC:
      return { ...state, metric: action.data };

    case SandboxActionsEnum.SET_METRIC_LOADING:
      return { ...state, isLoadingMetric: action.data };

    case SandboxActionsEnum.SET_PIPELINE_UID:
      return {
        ...state,
        pipelineUid: action.data.uid,
        pipelineFrom: action.data.from,
      };

    case SandboxActionsEnum.SET_RESULT:
      return { ...state, result: action.data };

    case SandboxActionsEnum.SET_RESULT_LOADING:
      return { ...state, isLoadingResult: action.data };

    default:
      return state;
  }
};

export default sandboxReducer;

import { analyticsAPI } from "../../API/analytics/analyticsAPI";
import { IMetric, IResult } from "../../API/analytics/analyticsInterface";
import { sandboxAPI } from "../../API/sanbox/sandboxAPI";
import { ICaseParams, IEpoch } from "../../API/sanbox/sandboxInterface";
import {
  PipelineFromType,
  SandboxActionsEnum,
  SetCaseParams,
  SetEpochs,
  SetEpochSelected,
  SetEpochsLoading,
  SetMetric,
  SetMetricLoading,
  SetPipelineUid,
  SetResult,
  SetResultLoading,
  ThunkType,
  ThunkTypeAsync,
} from "./sandbox-types";

export const actionsSandbox = {
  getCaseParams: (caseId: string): ThunkTypeAsync => {
    return async (dispatch) => {
      try {
        const params = await sandboxAPI.getSandboxParams(caseId);
        dispatch(actionsSandbox.setCaseParams(params));
      } catch (error) {
        console.log(error);
      }
    };
  },
  getEpochs:
    (caseId: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsSandbox.setEpochsLoading(true));
      try {
        const epochs = await sandboxAPI.getSandboxEpoch(caseId);
        dispatch(actionsSandbox.setEpochs(epochs));
        dispatch(actionsSandbox.setEpochsLoading(false));
      } catch (error) {
        console.log(error);
      }
    },
  getMetric:
    (caseId: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsSandbox.setMetricLoading(true));
      try {
        const metric = await analyticsAPI.getMetrics(caseId);
        dispatch(actionsSandbox.setMetric(metric));
      } catch (error) {
        console.log(error);
        dispatch(actionsSandbox.setMetric(null));
      } finally {
        dispatch(actionsSandbox.setMetricLoading(false));
      }
    },
  getResult:
    (caseId: string, pipelineId: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsSandbox.setResultLoading(true));
      try {
        const result = await analyticsAPI.getResults(caseId, pipelineId);
        dispatch(actionsSandbox.setResult(result));
      } catch (error) {
        console.log(error);
        dispatch(actionsSandbox.setResult(null));
      } finally {
        dispatch(actionsSandbox.setResultLoading(false));
      }
    },
  selectEpoch: (data: IEpoch): SetEpochSelected => ({
    type: SandboxActionsEnum.SET_EPOCH_SELECTED,
    data,
  }),
  setCaseParams: (data: ICaseParams): SetCaseParams => ({
    type: SandboxActionsEnum.SET_CASE_PARAMS,
    data,
  }),
  setEpochs: (data: IEpoch[]): SetEpochs => ({
    type: SandboxActionsEnum.SET_EPOCHS,
    data,
  }),
  setEpochsLoading: (data: boolean): SetEpochsLoading => ({
    type: SandboxActionsEnum.SET_EPOCHS_LOADING,
    data,
  }),
  setMetric: (data: IMetric | null): SetMetric => ({
    type: SandboxActionsEnum.SET_METRIC,
    data,
  }),
  setMetricLoading: (data: boolean): SetMetricLoading => ({
    type: SandboxActionsEnum.SET_METRIC_LOADING,
    data,
  }),
  setPipelineUid: (uid: string, from: PipelineFromType): SetPipelineUid => ({
    type: SandboxActionsEnum.SET_PIPELINE_UID,
    data: { uid, from },
  }),
  setResult: (data: IResult | null): SetResult => ({
    type: SandboxActionsEnum.SET_RESULT,
    data,
  }),
  setResultLoading: (data: boolean): SetResultLoading => ({
    type: SandboxActionsEnum.SET_RESULT_LOADING,
    data,
  }),
};

export const setPipelineUid =
  (uid: string, from: PipelineFromType): ThunkType =>
  (dispatch) => {
    dispatch(actionsSandbox.setPipelineUid(uid, from));
  };

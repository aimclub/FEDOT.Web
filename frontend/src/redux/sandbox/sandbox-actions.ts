import { analyticsAPI } from "../../API/analytics/analyticsAPI";
import { IMetric, IResult } from "../../API/analytics/analyticsInterface";
import { metaAPI } from "../../API/meta/metaAPI";
import { IModelName } from "../../API/meta/metaInterface";
import { sandboxAPI } from "../../API/sanbox/sandboxAPI";
import { ICaseParams, IEpoch } from "../../API/sanbox/sandboxInterface";
import { getPipeline, resetPipeline } from "../pipeline/pipeline-actions";
import { getShowCase } from "../showCase/showCase-actions";
import {
  SandboxActionsEnum,
  SetCaseParams,
  SetEpochs,
  SetEpochSelected,
  SetEpochsLoading,
  SetMetric,
  SetMetricLoading,
  SetModelNames,
  SetResult,
  SetResultLoading,
  ThunkTypeAsync,
} from "./sandbox-types";

export const actionsSandbox = {
  getCaseParams: (caseId: string): ThunkTypeAsync => {
    return async (dispatch) => {
      try {
        const params = await sandboxAPI.getSandboxParams(caseId);
        dispatch(actionsSandbox.setCaseParams(params));
        if (params) {
          dispatch(getModelNames(params.task_id));
        }
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
  setModelNames: (data: IModelName[]): SetModelNames => ({
    type: SandboxActionsEnum.SET_MODEL_NAMES,
    data,
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

export const getCase =
  (caseId: string): ThunkTypeAsync =>
  async (dispatch, getState) => {
    const { isFromHistory } = getState().pipeline;
    // console.log("isFromHistory", isFromHistory);
    if (!isFromHistory) dispatch(resetPipeline());
    const res =
      getState().showCase.showCase?.case_id !== caseId
        ? dispatch(getShowCase(caseId))
        : Promise.resolve();
    return res.then(() => {
      const { showCase } = getState().showCase;
      // console.log("case id", showCase?.case_id);
      if (showCase?.case_id) {
        dispatch(getPipeline(showCase.individual_id));
        if (!isFromHistory) {
          dispatch(actionsSandbox.getEpochs(showCase.case_id));
          dispatch(getResult(showCase.case_id, showCase.individual_id));
        }
        dispatch(actionsSandbox.getMetric(showCase.case_id));
        dispatch(actionsSandbox.getCaseParams(showCase.case_id));
      }
    });
  };

export const getModelNames =
  (taskId: string): ThunkTypeAsync =>
  async (dispatch) => {
    try {
      const modelNames = await metaAPI.getAllModelName(taskId);
      dispatch(actionsSandbox.setModelNames(modelNames));
    } catch (error) {
      console.log(error);
      return Promise.reject(error);
    }
  };

export const getResult =
  (caseId: string, individualId: string): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsSandbox.setResultLoading(true));
    try {
      const result = await analyticsAPI.getResults(caseId, individualId);
      dispatch(actionsSandbox.setResult(result));
    } catch (error) {
      console.log(error);
      dispatch(actionsSandbox.setResult(null));
    } finally {
      dispatch(actionsSandbox.setResultLoading(false));
    }
  };

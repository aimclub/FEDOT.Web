import { ThunkAction } from "redux-thunk";
import { sandBoxAPI } from "../../../API/sandBox/sandBoxAPI";
import { StateType } from "../../store";
import { IEpoch } from "./../../../API/sandBox/sandBoxInterface";
import { analyticsAPI } from "./../../../API/analytics/analyticsAPI";
import { IMetric, IResult } from "../../../API/analytics/analyticsInterface";

const SANDBOX_EPOCHS = "SANDBOX_EPOCHS";
const SANDBOX_EPOCH_SELCTED = "SANDBOX_EPOCH_SELCTED";
const SANDBOX_RESULTS = "SANDBOX_RESULTS";
const SANDBOX_METRICS = "SANDBOX_METRICS";
const SANDBOX_HISTORY = "SANDBOX_HISTORY";

let initialState = {
  sandBox_epochs: null as IEpoch[] | null,
  sandBox_epochs_selected: null as IEpoch | null,
  sandbox_results: null as IResult | null,
  sandbox_metrics: null as IMetric | null,
  sandbox_history: false,
};

export type InitialStateType = typeof initialState;
type AllTyps =
  | EpochsArrType
  | EpochsSelectedType
  | ResultsType
  | MetricsType
  | HistipyType;

const sandBoxReducer = (
  state = initialState,
  action: AllTyps
): InitialStateType => {
  switch (action.type) {
    case SANDBOX_EPOCHS:
      return { ...state, sandBox_epochs: action.data };
    case SANDBOX_EPOCH_SELCTED:
      return { ...state, sandBox_epochs_selected: action.data };
    case SANDBOX_RESULTS:
      return { ...state, sandbox_results: action.data };
    case SANDBOX_METRICS:
      return { ...state, sandbox_metrics: action.data };
    case SANDBOX_HISTORY:
      return { ...state, sandbox_history: action.data };

    default:
      return state;
  }
};

type EpochsArrType = {
  type: typeof SANDBOX_EPOCHS;
  data: IEpoch[] | null;
};
type EpochsSelectedType = {
  type: typeof SANDBOX_EPOCH_SELCTED;
  data: IEpoch | null;
};
type ResultsType = {
  type: typeof SANDBOX_RESULTS;
  data: IResult | null;
};
type MetricsType = {
  type: typeof SANDBOX_METRICS;
  data: IMetric | null;
};
type HistipyType = {
  type: typeof SANDBOX_HISTORY;
  data: boolean;
};

export const actionsSandBox = {
  epochsArr: (data: IEpoch[] | null): EpochsArrType => ({
    type: SANDBOX_EPOCHS,
    data,
  }),
  epochsSelected: (data: IEpoch | null): EpochsSelectedType => ({
    type: SANDBOX_EPOCH_SELCTED,
    data,
  }),
  results: (data: IResult | null): ResultsType => ({
    type: SANDBOX_RESULTS,
    data,
  }),
  metrics: (data: IMetric | null): MetricsType => ({
    type: SANDBOX_METRICS,
    data,
  }),
  historyToggle: (data: boolean): HistipyType => ({
    type: SANDBOX_HISTORY,
    data,
  }),
};

type ThunkTypeAsync = ThunkAction<Promise<void>, StateType, unknown, AllTyps>;
type ThunkType = ThunkAction<void, StateType, unknown, AllTyps>;

export const getEpochs = (caseId: string): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      let epochs = await sandBoxAPI.getSandBoxEpoch(caseId);
      dispatch(actionsSandBox.epochsArr(epochs));
    } catch (err) {
      console.error(err);
    }
  };
};

export const setSelectedEpoch = (epoch: IEpoch): ThunkType => {
  return (dispatch) => {
    dispatch(actionsSandBox.epochsSelected(epoch));
  };
};

export const getResults = (
  caseId: string,
  pipelineId: string
): ThunkTypeAsync => {
  // console.log(`caseId`, caseId);
  return async (dispatch) => {
    dispatch(actionsSandBox.results(null));
    try {
      let results = await analyticsAPI.getResults(caseId, pipelineId);
      dispatch(actionsSandBox.results(results));
    } catch (err) {
      console.error(err);
    }
  };
};

export const getMetrics = (caseId: string): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      let metrics = await analyticsAPI.getMetrics(caseId);
      dispatch(actionsSandBox.metrics(metrics));
    } catch (err) {
      console.error(err);
    }
  };
};

export const setHistoryToggle = (data: boolean): ThunkType => {
  return (dispatch) => {
    dispatch(actionsSandBox.historyToggle(data));
  };
};

export default sandBoxReducer;

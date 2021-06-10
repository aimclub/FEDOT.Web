import { StateType } from "./store";
import { ThunkAction } from "redux-thunk";
import { IHistoryGraph, IMainGraph, sandboxAPI } from "../api/sandbox";

const SET_MAIN_GRAPH = "SET_MAIN_GRAPH";
const SET_HISTORY_GRAPH = "SET_HISTORY_GRAPH";

let initialState = {
  mainGraph: { nodes: [], edges: [] } as IMainGraph,
  historyGraph: { nodes: [], edges: [] } as IHistoryGraph,
};

export type InitialStateDatasetsType = typeof initialState;
type AllTypes = SetMainGraphType | SetHistoryGraphType;

const sandboxReducer = (
  state = initialState,
  action: AllTypes
): InitialStateDatasetsType => {
  switch (action.type) {
    case SET_MAIN_GRAPH:
      return { ...state, mainGraph: action.data };
    case SET_HISTORY_GRAPH:
      return {
        ...state,
        historyGraph: action.data,
      };
    default:
      return state;
  }
};

type SetMainGraphType = {
  type: typeof SET_MAIN_GRAPH;
  data: IMainGraph;
};
type SetHistoryGraphType = {
  type: typeof SET_HISTORY_GRAPH;
  data: IHistoryGraph;
};

export const actionsSandbox = {
  setMainGraph: (data: IMainGraph): SetMainGraphType => ({
    type: SET_MAIN_GRAPH,
    data,
  }),
  setHistoryGraph: (data: IHistoryGraph): SetHistoryGraphType => ({
    type: SET_HISTORY_GRAPH,
    data,
  }),
};
// для async
type ThunkTypeAsync = ThunkAction<Promise<void>, StateType, unknown, AllTypes>;

export const getMainGraph = (uid: number): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      let data = await sandboxAPI.getMainGraph(uid);
      dispatch(actionsSandbox.setMainGraph(data));
    } catch (err) {
      return Promise.reject(err);
    }
  };
};

export const getHistoryGraph = (uid: number): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      let data = await sandboxAPI.getHistoryGraph(uid);
      dispatch(actionsSandbox.setHistoryGraph(data));
    } catch (err) {
      return Promise.reject(err);
    }
  };
};

export default sandboxReducer;

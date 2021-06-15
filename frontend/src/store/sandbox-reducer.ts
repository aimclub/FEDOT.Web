import { StateType } from "./store";
import { ThunkAction } from "redux-thunk";
import { IHistoryGraph, IMainGraph, sandboxAPI } from "../api/sandbox";
import { NodeDataType } from "../components/DirectedGraph/DirectedGraph";

const SET_MAIN_GRAPH = "SET_MAIN_GRAPH";
const SET_HISTORY_GRAPH = "SET_HISTORY_GRAPH";
const DELETE_NODE_MAIN_GRAPH = "DELETE_NODE_MAIN_GRAPH";
const ADD_NODE_MAIN_GRAPH = "ADD_NODE_MAIN_GRAPH";
const TOGGLE_EDIT_MODAL = "TOGGLE_EDIT_MODAL";

let initialState = {
  mainGraph: { nodes: [], edges: [] } as IMainGraph,
  historyGraph: { nodes: [], edges: [] } as IHistoryGraph,
  isOpenEditModal: false,
};

export type InitialStateDatasetsType = typeof initialState;
type AllTypes =
  | SetMainGraphType
  | SetHistoryGraphType
  | DeleteNodeMainGraphType
  | AddNodeMainGraphType
  | ToggleEditModalType;

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
    case DELETE_NODE_MAIN_GRAPH: {
      return {
        ...state,
        mainGraph: {
          ...state.mainGraph,
          nodes: [...state.mainGraph.nodes].filter((item) => {
            return item.id !== +action.data;
          }),
        },
      };
    }
    case ADD_NODE_MAIN_GRAPH:
      return {
        ...state,
        mainGraph: {
          ...state.mainGraph,
          nodes: [...state.mainGraph.nodes, ...action.data.nodes],
          edges: [...state.mainGraph.edges, ...action.data.edges],
        },
      };
    case TOGGLE_EDIT_MODAL: {
      console.log(`### state`, state);
      console.log(`### !state.isOpenEditModal`, !state.isOpenEditModal);
      return {
        ...state,
        isOpenEditModal: !state.isOpenEditModal,
      };
    }

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
type DeleteNodeMainGraphType = {
  type: typeof DELETE_NODE_MAIN_GRAPH;
  data: number;
};
type AddNodeMainGraphType = {
  type: typeof ADD_NODE_MAIN_GRAPH;
  data: IMainGraph;
};
type ToggleEditModalType = {
  type: typeof TOGGLE_EDIT_MODAL;
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
  deleteNodeMainGraph: (data: number): DeleteNodeMainGraphType => ({
    type: DELETE_NODE_MAIN_GRAPH,
    data,
  }),
  addNodeMainGraph: (data: IMainGraph): AddNodeMainGraphType => ({
    type: ADD_NODE_MAIN_GRAPH,
    data,
  }),
  toggleEditModal: (): ToggleEditModalType => ({
    type: TOGGLE_EDIT_MODAL,
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

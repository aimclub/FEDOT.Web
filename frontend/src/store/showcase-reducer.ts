import { StateType } from "./store";
import { ThunkAction } from "redux-thunk";
import { IHistoryGraph, IMainGraph, sandboxAPI } from "../api/sandbox";
import { showcaseAPI, ShowcasesType } from "../api/showcase";

const SET_SHOWCASES = "SET_SHOWCASES";

let initialState = {
  showcases: {} as ShowcasesType,
};

export type InitialStateDatasetsType = typeof initialState;
type AllTypes = SetShowcasesType;

const showcaseReducer = (
  state = initialState,
  action: AllTypes
): InitialStateDatasetsType => {
  switch (action.type) {
    case SET_SHOWCASES:
      return { ...state, showcases: action.data };
    default:
      return state;
  }
};

type SetShowcasesType = {
  type: typeof SET_SHOWCASES;
  data: ShowcasesType;
};

export const actionsShowcase = {
  setShowcases: (data: ShowcasesType): SetShowcasesType => ({
    type: SET_SHOWCASES,
    data,
  }),
};
// для async
type ThunkTypeAsync = ThunkAction<Promise<void>, StateType, unknown, AllTypes>;

export const getShowcases = (): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      let data = await showcaseAPI.getShowcases();
      dispatch(actionsShowcase.setShowcases(data));
    } catch (err) {
      return Promise.reject(err);
    }
  };
};

export default showcaseReducer;

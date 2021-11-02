import { ThunkAction } from "redux-thunk";
import { ICase, ICaseItem } from "../../API/showcase/showcaseInterface";
import { StateType } from "../store";
import { initialState } from "./showCase-reducer";

export enum CaseActionsEnum {
  ALL_CASES = "ALL_CASES",
  LOADING_CASE = "LOADING_CASE",
  SHOW_CASE = "SHOW_CASE",
}

export type InitialStateType = typeof initialState;

export type ThunkTypeAsync = ThunkAction<
  Promise<void>,
  StateType,
  unknown,
  AllTypes
>;

export type ThunkType = ThunkAction<void, StateType, unknown, AllTypes>;

export type AllTypes =
  | SetAllCases
  | SetLoadingCase
  | SetShowCase;

export type SetAllCases = {
  type: CaseActionsEnum.ALL_CASES;
  data: ICaseItem[];
};

export type SetLoadingCase = {
  type: CaseActionsEnum.LOADING_CASE;
  data: boolean;
};

export type SetShowCase = {
  type: CaseActionsEnum.SHOW_CASE;
  data: ICase | null;
};

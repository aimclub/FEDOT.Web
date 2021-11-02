import { ThunkAction } from "redux-thunk";
import { StateType } from "../store";
import { initialState } from "./auth-reducer";

export enum AuthActionsEnum {
  SET_AUTH = "SET_AUTH",
  SET_ERROR = "SET_ERROR",
  SET_LOADING = "SET_LOADING",
  SET_TOKEN = "SET_TOKEN",
  SET_USER_DATA = "SET_USER_DATA",
}

export interface IUser {
  login: string;
}

export type InitialStateType = typeof initialState;

export type ThunkTypeAsync = ThunkAction<
  Promise<void>,
  StateType,
  unknown,
  AllTypes
>;

export type ThunkType = ThunkAction<void, StateType, unknown, AllTypes>;

export type AllTypes = SetAuth | SetError | SetLoading | SetToken | SetUserData;

export type SetAuth = {
  type: AuthActionsEnum.SET_AUTH;
  data: boolean;
};

export type SetError = {
  type: AuthActionsEnum.SET_ERROR;
  data: string | null;
};

export type SetLoading = {
  type: AuthActionsEnum.SET_LOADING;
  data: boolean;
};

export type SetToken = {
  type: AuthActionsEnum.SET_TOKEN;
  data: string;
};

export type SetUserData = {
  type: AuthActionsEnum.SET_USER_DATA;
  data: IUser;
};

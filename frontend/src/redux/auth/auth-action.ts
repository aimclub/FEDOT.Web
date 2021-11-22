import { authAPI } from "../../API/auth/authAPI";
import {
  AuthActionsEnum,
  IUser,
  SetAuth,
  SetError,
  SetLoading,
  SetToken,
  SetUserData,
  ThunkType,
  ThunkTypeAsync,
} from "./auth-types";

export const actionsAuth = {
  logOut: (): ThunkType => (dispatch) => {
    dispatch(actionsAuth.setToken(""));
    dispatch(actionsAuth.setUser({} as IUser));
    dispatch(actionsAuth.setAuth(false));
  },
  register:
    (login: string, password: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsAuth.setLoading(true));
      dispatch(actionsAuth.setError(null));
      dispatch(actionsAuth.setToken(""));
      dispatch(actionsAuth.setUser({} as IUser));
      try {
        const res = await authAPI.signUp(login, password);
        if (res) {
          const { token_value } = await authAPI.signIn(login, password);
          dispatch(actionsAuth.setToken(token_value));
          dispatch(actionsAuth.setAuth(true));
          dispatch(actionsAuth.setUser({ login }));
        }
      } catch (error) {
        dispatch(actionsAuth.setError((error as Error).message));
        console.log(error);
      } finally {
        dispatch(actionsAuth.setLoading(false));
      }
    },
  setAuth: (data: boolean): SetAuth => ({
    type: AuthActionsEnum.SET_AUTH,
    data,
  }),
  setError: (data: string | null): SetError => ({
    type: AuthActionsEnum.SET_ERROR,
    data,
  }),
  setLoading: (data: boolean): SetLoading => ({
    type: AuthActionsEnum.SET_LOADING,
    data,
  }),
  setToken: (data: string): SetToken => ({
    type: AuthActionsEnum.SET_TOKEN,
    data,
  }),
  setUser: (data: IUser): SetUserData => ({
    type: AuthActionsEnum.SET_USER_DATA,
    data,
  }),
  singIn:
    (login: string, password: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsAuth.setLoading(true));
      dispatch(actionsAuth.setError(null));
      dispatch(actionsAuth.setToken(""));
      dispatch(actionsAuth.setAuth(false));
      try {
        const { token_value } = await authAPI.signIn(login, password);
        dispatch(actionsAuth.setToken(token_value));
        dispatch(actionsAuth.setAuth(true));
        dispatch(actionsAuth.setUser({ login }));
      } catch (error) {
        dispatch(actionsAuth.setError((error as Error).message));
        console.log(error);
      } finally {
        dispatch(actionsAuth.setLoading(false));
      }
    },
};

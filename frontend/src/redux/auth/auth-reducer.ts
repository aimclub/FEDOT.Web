import {
  AllTypes,
  AuthActionsEnum,
  InitialStateType,
  IUser,
} from "./auth-types";

export const initialState = {
  authError: null as string | null,
  isAuth: false,
  isLoading: false,
  token: "",
  user: {} as IUser,
};

const authReducer = (
  state = initialState,
  action: AllTypes
): InitialStateType => {
  switch (action.type) {
    case AuthActionsEnum.SET_AUTH:
      return { ...state, isAuth: action.data };

    case AuthActionsEnum.SET_ERROR:
      return { ...state, authError: action.data };

    case AuthActionsEnum.SET_LOADING:
      return { ...state, isLoading: action.data };

    case AuthActionsEnum.SET_TOKEN:
      return { ...state, token: action.data };

    case AuthActionsEnum.SET_USER_DATA:
      return { ...state, user: action.data };

    default:
      return state;
  }
};

export default authReducer;

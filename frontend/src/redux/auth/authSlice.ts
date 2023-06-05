import { createSlice } from "@reduxjs/toolkit";
import { authAPI } from "../../API/auth/authAPI";

export interface IUser {
  username: string;
}

export const initialState = {
  isAuth: false,
  token: null as string | null,
  user: null as IUser | null,
};

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout: (state) => {
      state.isAuth = false;
      state.token = null;
      state.user = null;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      authAPI.endpoints.signin.matchFulfilled,
      (state, { payload, meta }) => {
        state.isAuth = true;
        state.token = payload.token_value;
        state.user = { username: meta.arg.originalArgs.email };
      }
    );
    builder.addMatcher(authAPI.endpoints.signin.matchRejected, (state) => {
      state.isAuth = false;
      state.token = null;
      state.user = null;
    });
  },
});

export const { logout } = authSlice.actions;
export const { reducer: authReducer, name: authReducerName } = authSlice;

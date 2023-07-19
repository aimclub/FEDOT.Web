import { combineReducers, configureStore } from "@reduxjs/toolkit";

// ---redux-persist---
import {
  FLUSH,
  PAUSE,
  PERSIST,
  persistReducer,
  persistStore,
  PURGE,
  REGISTER,
  REHYDRATE,
} from "redux-persist";
// import storage from "redux-persist/lib/storage"; // localStorage
import storage from "redux-persist/lib/storage/session"; // sessionStorage

// --- api ---

import { commonApi } from "../API/baseURL";

// --- reducers ---

import { authReducer, authReducerName } from "./auth/authSlice";
import { showcaseReducer, showcaseReducerName } from "./showCase/showcaseSlice";
import { sandboxReducer, sandboxReducerName } from "./sandbox/sandboxSlice";

// import authReducer from "./auth/auth-reducer";
// import showCaseReducer from "./showCase/showCase-reducer";
// import sandboxReducer from "./sandbox/sandbox-reducer";
// import pipelineReducer from "./pipeline/pipeline-reducer";
// import historyReducer from "./history/history-reducer";

const rootReducer = combineReducers({
  [authReducerName]: authReducer,
  [showcaseReducerName]: showcaseReducer,
  [sandboxReducerName]: sandboxReducer,
  // sandbox: sandboxReducer,
  // pipeline: pipelineReducer,
  // history: historyReducer,
  [commonApi.reducerPath]: commonApi.reducer,
});

const persistConfig = {
  key: "root",
  storage,
  whitelist: [authReducerName, showcaseReducerName],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

const setupStore = () => {
  return configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(commonApi.middleware),
  });
};

export const store = setupStore();
export const persistor = persistStore(store);

export type RootState = ReturnType<typeof rootReducer>;
export type AppStore = ReturnType<typeof setupStore>;
export type AppDispatch = AppStore["dispatch"];

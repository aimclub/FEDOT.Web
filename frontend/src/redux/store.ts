import { applyMiddleware, combineReducers, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { composeWithDevTools } from "redux-devtools-extension";

// redux-persist---
import { persistStore, persistReducer } from "redux-persist";
// import storage from "redux-persist/lib/storage"; // defaults to localStorage for web
import storage from "redux-persist/lib/storage/session"; // sessionStorage

//------
import authReducer from "./auth/auth-reducer";
import showCaseReducer from "./showCase/showCase-reducer";
import sandboxReducer from "./sandbox/sandbox-reducer";
import pipelineReducer from "./pipeline/pipeline-reducer";
import historyReducer from "./history/history-reducer";

const persistConfig = {
  key: "root",
  storage,
  whitelist: ["auth", "showCase"], //массив для редьюсеров, которые не должны сбрасываться при обновлении
};

let reducers = combineReducers({
  auth: authReducer,
  showCase: showCaseReducer,
  sandbox: sandboxReducer,
  pipeline: pipelineReducer,
  history: historyReducer,
});

type RootReducerType = typeof reducers;
export type StateType = ReturnType<RootReducerType>;

const persistedReducer = persistReducer(persistConfig, reducers); // redux-persist--- сохраняет состояние при обновлении

const store = () => {
  let store = createStore(
    persistedReducer,
    composeWithDevTools(applyMiddleware(thunkMiddleware))
  );
  //@ts-ignore
  let persistor = persistStore(store);
  return { store, persistor };
};

export default store;

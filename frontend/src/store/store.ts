import { applyMiddleware, combineReducers, createStore } from "redux";
import thunkMiddleware from "redux-thunk";
import { composeWithDevTools } from "redux-devtools-extension";
import sandboxReducer from "./sandbox-reducer";

let reducers = combineReducers({
  sandboxReducer,
});

type RootReducerType = typeof reducers;

export type StateType = ReturnType<RootReducerType>;

let store = createStore(
  reducers,
  composeWithDevTools(applyMiddleware(thunkMiddleware))
);

export default store;

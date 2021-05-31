import { configureStore, getDefaultMiddleware } from "@reduxjs/toolkit";
import showcaseReducer from "./showcaseSlice";
import sandboxReducer from "./sandboxSlice";

const store = configureStore({
  reducer: {
    showcase: showcaseReducer,
    sandbox: sandboxReducer,
  },
  middleware: getDefaultMiddleware(),
});

export default store;

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;

// Inferred type: {posts: PostsState, comments: CommentsState, users: UsersState}
export type AppDispatch = typeof store.dispatch;

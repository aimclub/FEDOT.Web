import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { IMainGraph, sandboxAPI } from "../api/sandbox";

export const getMainGraph = createAsyncThunk(
  "sandbox/getMainGraph",
  async () => {
    try {
      const res = await sandboxAPI.getMainGraph(54545);
      console.log(`### res`, res);
      return res as IMainGraph;
    } catch (err) {
      console.log(`### err.message`, err.message);
    }
  }
);

export const sandboxSlice = createSlice({
  name: "sandbox",
  initialState: {
    mainGraph: {
      nodes: [],
      edges: [],
    } as IMainGraph,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(getMainGraph.fulfilled, (state, action) => {
      console.log(`### action.payload`, action.payload);
      if (action.payload) {
        state.mainGraph = action.payload;
      }
    });
  },
});

// Action creators are generated for each case reducer function
export const {} = sandboxSlice.actions;

export default sandboxSlice.reducer;

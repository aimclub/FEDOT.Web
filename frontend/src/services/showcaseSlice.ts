import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import { CaseItemType, showcaseAPI, ShowcasesType } from "../api/showcase";

export const getShowcases = createAsyncThunk(
  "showcase/getShowcases",
  async () => {
    try {
      return await showcaseAPI.getShowcases();
    } catch (err) {
      console.log(`### err.message`, err.message);
    }
  }
);

export const getShowcasesItem = createAsyncThunk(
  "showcase/getShowcases",
  async (id: string) => {
    try {
      return await showcaseAPI.getShowcasesItem(id);
    } catch (err) {
      console.log(`### err.message`, err.message);
    }
  }
);

export const showcaseSlice = createSlice({
  name: "showcase",
  initialState: {
    showcases: {} as ShowcasesType,
    showcaseItem: {} as CaseItemType,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(getShowcases.fulfilled, (state, action) => {
      state.showcases = action.payload as ShowcasesType;
    });
    // builder.addCase(getShowcasesItem.fulfilled, (state, action) => {
    //   state.showcaseItem = action.payload as CaseItemType;
    // });
  },
});

// Action creators are generated for each case reducer function
export const {} = showcaseSlice.actions;

export default showcaseSlice.reducer;

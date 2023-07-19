import { PayloadAction, createSlice } from "@reduxjs/toolkit";
export const initialState = {
  selected_showcase_id: "",
};

export const showcaseSlice = createSlice({
  name: "showcase",
  initialState,
  reducers: {
    setSelectedShowcase: (
      state,
      { payload }: PayloadAction<{ caseId: string }>
    ) => {
      state.selected_showcase_id = payload.caseId;
    },
  },
});

export const { setSelectedShowcase } = showcaseSlice.actions;
export const { reducer: showcaseReducer, name: showcaseReducerName } =
  showcaseSlice;

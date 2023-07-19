import { commonApi } from "../baseURL";
import { IHistoryGraph } from "./composerInterface";

export const composerAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    getHistoryGraph: build.query<IHistoryGraph, { caseId: string }>({
      query: ({ caseId }) => ({
        url: `/composer/${caseId}`,
      }),
      providesTags: ["case"],
    }),
  }),
});

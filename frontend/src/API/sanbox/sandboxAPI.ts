import { commonApi } from "../baseURL";
import { ICaseParams, IEpoch } from "./sandboxInterface";

export const sandboxAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    getSandboxEpoch: build.query<IEpoch[], { caseId: string }>({
      query: ({ caseId }) => ({ url: `/sandbox/epoch/${caseId}` }),
    }),
    // getShowcase: build.query<ICase, { caseId: string }>({
    //   query: ({ caseId }) => ({
    //     url: `/showcase/items/${caseId}`,
    //   }),
    // }),
    getSandboxParams: build.query<ICaseParams, { caseId: string }>({
      query: ({ caseId }) => ({ url: `/sandbox/params/${caseId}` }),
    }),
  }),
});

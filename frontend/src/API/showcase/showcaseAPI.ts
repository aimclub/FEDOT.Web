import { commonApi } from "../baseURL";
import { ICase, ICaseItem } from "./showcaseInterface";

export const showcaseAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    getAllShowcases: build.query<ICaseItem[], undefined>({
      query: () => ({ url: "showcase/" }),
    }),
    getShowcase: build.query<ICase, { caseId: string }>({
      query: ({ caseId }) => ({
        url: `/showcase/items/${caseId}`,
      }),
    }),
  }),
});

import { commonApi } from "../baseURL";
import { IModelName } from "./metaInterface";

export const metaAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    // getAllMetricName: build.query<IMetricName[], { taskId: string }>({
    //   query: ({ taskId }) => ({ url: `/meta/metrics/${taskId}` }),
    // }),

    getAllModelName: build.query<IModelName[], { taskId: string }>({
      query: ({ taskId }) => ({ url: `/meta/models/${taskId}` }),
    }),

    // getAllTask: build.query<ITask[], undefined>({
    //   query: () => ({ url: `/meta/tasks` }),
    // }),
  }),
});

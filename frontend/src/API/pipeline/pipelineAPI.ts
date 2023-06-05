import { commonApi } from "../baseURL";
import {
  IAdd,
  IPipeline,
  IPipelineImage,
  IValidate,
} from "./pipelineInterface";

export const pipelineAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    getPipeline: build.query<IPipeline, { uid: string }>({
      query: ({ uid }) => ({
        url: `/pipelines/${uid}`,
      }),
      providesTags: ["case"],
    }),
    validatePipeline: build.mutation<IValidate, IPipeline>({
      query: (pipeline) => ({
        url: `/pipelines/validate`,
        method: "POST",
        body: {
          uid: pipeline.uid,
          nodes: pipeline.nodes,
          edges: pipeline.edges,
        },
      }),
    }),
    addPipeline: build.mutation<IAdd, IPipeline>({
      query: (pipeline) => ({
        url: `/pipelines/add`,
        method: "POST",
        body: {
          uid: pipeline.uid,
          nodes: pipeline.nodes,
          edges: pipeline.edges,
        },
      }),
    }),
    getPipelineImage: build.query<IPipelineImage, { uid: string }>({
      query: ({ uid }) => ({
        url: `/pipelines/image/${uid}`,
      }),
      providesTags: ["case"],
    }),
  }),
});

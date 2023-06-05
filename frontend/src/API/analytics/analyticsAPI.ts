import { commonApi } from "../baseURL";
import {
  GenerationType,
  IGeneration,
  IMetric,
  IResult,
} from "./analyticsInterface";

export const analyticsAPI = commonApi.injectEndpoints({
  endpoints: (build) => ({
    getCaseMetric: build.query<IMetric, { caseId: string }>({
      query: ({ caseId }) => ({
        url: `/analytics/quality/${caseId}`,
      }),
    }),
    getPipelineResult: build.query<
      IResult,
      { caseId: string; pipeline_uid: string }
    >({
      query: ({ caseId, pipeline_uid }) => ({
        url: `/analytics/results/${caseId}/${pipeline_uid}`,
      }),
    }),
    getGenerations: build.query<
      IGeneration,
      { caseId: string; type: GenerationType }
    >({
      query: ({ caseId, type }) => ({
        url: `/analytics/generations/${caseId}/${type}`,
      }),
    }),
  }),
});

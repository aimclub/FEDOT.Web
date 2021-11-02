import { instance } from "../baseURL";
import {
  GenerationType,
  IGeneration,
  IMetric,
  IResult,
} from "./analyticsInterface";

export const analyticsAPI = {
  async getGenerations(caseId: string, type: GenerationType) {
    try {
      const res = await instance.get<IGeneration>(
        `/analytics/generations/${caseId}/${type}`
      );
      return res.data;
    } catch (error: any) {
      return Promise.reject(error);
    }
  },
  async getMetrics(caseId: string) {
    try {
      const res = await instance.get<IMetric>(`/analytics/quality/${caseId}`);
      return res.data;
    } catch (error: any) {
      return Promise.reject(error);
    }
  },
  async getResults(caseId: string, pipelineId: string) {
    try {
      const res = await instance.get<IResult>(
        `/analytics/results/${caseId}/${pipelineId}`
      );
      return res.data;
    } catch (error: any) {
      return Promise.reject(error);
    }
  },
};

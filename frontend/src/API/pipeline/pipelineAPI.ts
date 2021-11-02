import { instance } from "../baseURL";
import {
  IAdd,
  IPipeline,
  IPipelineImage,
  IValidate,
} from "./pipelineInterface";

export const pipelineAPI = {
  async getPipeline(uid: string) {
    try {
      const res = await instance.get<IPipeline>(`/pipelines/${uid}`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async getPipelineImage(uid: string) {
    try {
      const res = await instance.get<IPipelineImage>(`/pipelines/image/${uid}`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async validatePipeline(data: IPipeline) {
    try {
      const res = await instance.post<IValidate>(`/pipelines/validate`, data);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async postPipeline(data: IPipeline) {
    try {
      const res = await instance.post<IAdd>(`/pipelines/add`, data);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
};

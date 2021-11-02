import { instance } from "../baseURL";
import { IMetricName, IModelName, ITask } from "./metaInterface";

export const metaAPI = {
  async getAllMetricName(taskId: string) {
    try {
      const res = await instance.get<IMetricName[]>(`/meta/metrics/${taskId}`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async getAllModelName(taskId: string) {
    try {
      const res = await instance.get<IModelName[]>(`/meta/models/${taskId}`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async getAllTask() {
    try {
      const res = await instance.get<ITask[]>(`/meta/tasks`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
};

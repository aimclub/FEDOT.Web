import { instance } from "../baseURL";
import { IHistoryGraph } from "./composerInterface";

export const composerAPI = {
  async getHistoryGraph(caseId: string) {
    try {
      const res = await instance.get<IHistoryGraph>(`/composer/${caseId}`);
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
};

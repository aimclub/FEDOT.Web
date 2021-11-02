import { instance } from "../baseURL";
import { ICase, ICaseItem } from "./showcaseInterface";

export const showCasesAPI = {
  async getAllShowCases() {
    try {
      const res = await instance.get<ICaseItem[]>(`/showcase/`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  async getShowCase(caseId: string) {
    try {
      const res = await instance.get<ICase>(`/showcase/items/${caseId}`);
      return res.data;
    } catch (error) {
      return Promise.reject(error);
    }
  },
};

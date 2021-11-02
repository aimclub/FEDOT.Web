import { instance } from "../baseURL";
import { ICaseParams, IEpoch } from "./sandboxInterface";

export const sandboxAPI = {
  async getSandboxEpoch(caseId: string) {
    try {
      const res = await instance.get<IEpoch[]>(`/sandbox/epoch/${caseId}`);
      return res.data;
    } catch (error: any) {
      return Promise.reject(error);
    }
  },
  async getSandboxParams(caseId: string) {
    try {
      const res = await instance.get<ICaseParams>(`/sandbox/params/${caseId}`);
      return res.data;
    } catch (error: any) {
      return Promise.reject(error);
    }
  },
};

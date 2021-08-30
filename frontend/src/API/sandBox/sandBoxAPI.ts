import { instance } from "../baseURL";
import { IEpoch } from "./sandBoxInterface";

export const sandBoxAPI = {
  async getSandBoxEpoch(caseId: string) {
    try {
      const res = await instance.get<IEpoch[]>(`/sandbox/epoch/${caseId}`);
      return res.data;
    } catch (error) {
      console.error(`error`, error.response.data);
      return Promise.reject(error);
    }
  },
};
//   return instance
//     .get<ICaseArr[]>(`sandbox/epoch/${caseId}`)
//     .then((res) => {
//       // console.log("res.headers", res);
//       return res.data;
//     })
//     .catch((error: any) => {
//       console.error(`error`, error.response.data);
//       return Promise.reject(error);
//     });
// }}

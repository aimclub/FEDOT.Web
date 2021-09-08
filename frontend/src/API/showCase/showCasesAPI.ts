import {instance} from "../baseURL";
import {ICase, ICaseArr} from "./showCasesInterface";

const BASE_URL: string | undefined = process.env.REACT_APP_BASE_URL;

export const showCasesAPI = {
    getShowCasesArr() {
        return instance
            .get<ICaseArr[]>(`${BASE_URL}/showcase/`)
            .then((res) => {
                // console.log("res.headers", res);
                return res.data;
            })
            .catch((error: any) => {
                console.error(`error`, error.response.data);
                return Promise.reject(error);
            });
    },
    getShowCaseById(caseId: string) {
        return instance
            .get<ICase>(`showcase/items/${caseId}`)
            .then((res) => {
                return res.data;
            })
      .catch((error: any) => {
        // console.error(`error`, error.response.data);
        return Promise.reject(error);
      });
  },
};

import { instance } from "./index";

export type ShowcasesType = {
  items_uids: string[];
};

export type CaseItemType = {
  description: string;
  chain_id: string;
  icon_path: string;
  case_id: string;
};

export const showcaseAPI = {
  async getShowcases() {
    try {
      const res = await instance.get<ShowcasesType>("api/showcase");
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
  async getShowcasesItem(caseId: string) {
    try {
      const res = await instance.get<CaseItemType>(
        "api/showcase/items/" + caseId
      );
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
};

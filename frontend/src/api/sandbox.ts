import { instance } from "./index";
import {
  EdgeDataType,
  NodeDataType,
} from "../components/DirectedGraph/DirectedGraph";
import {
  HistoryEdgeType,
  HistoryNodeIndividualType,
  HistoryNodeOperatorType,
} from "../components/History/History";

export interface IMainGraph {
  nodes: NodeDataType[];
  edges: EdgeDataType[];
}

export interface IHistoryGraph {
  nodes: (HistoryNodeIndividualType | HistoryNodeOperatorType)[];
  edges: HistoryEdgeType[];
}

export const sandboxAPI = {
  async getMainGraph(uid: number) {
    try {
      const res = await instance.get<IMainGraph>("api/chains/" + uid);
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
  async getHistoryGraph(uid: number) {
    try {
      const res = await instance.get<IHistoryGraph>("api/composer/" + uid);
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
};

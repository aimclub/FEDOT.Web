import { instance } from "./index";
import {
  EdgeDataType,
  NodeDataType,
} from "../components/GraphEditor/GraphEditorDirectedGraph/GraphEditorDirectedGraph";
import {
  HistoryEdgeType,
  HistoryNodeIndividualType,
  HistoryNodeOperatorType,
} from "../components/HistoryGraph/HistoryGraph";

export interface IMainGraph {
  nodes: NodeDataType[];
  edges: EdgeDataType[];
}

export interface IHistoryGraph {
  nodes: (HistoryNodeIndividualType | HistoryNodeOperatorType)[];
  edges: HistoryEdgeType[];
}

export interface IChainImage {
  image_url: string;
  uid: string;
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
  async getChainsImage(uid: string) {
    try {
      const res = await instance.get<IChainImage>("api/chains/image/" + uid);
      return res.data;
    } catch (err) {
      return Promise.reject(err);
    }
  },
};

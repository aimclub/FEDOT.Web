import { instance } from "./index";
import {
  EdgeDataType,
  NodeDataType,
} from "../components/DirectedGraph/DirectedGraph";

export interface IMainGraph {
  nodes: NodeDataType[];
  edges: EdgeDataType[];
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
};

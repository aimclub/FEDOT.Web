import { INodeData } from "../API/pipeline/pipelineInterface";
import { useAppSelector } from "./redux";

export const useGetPipelineNode = (): INodeData | null =>
  useAppSelector((state) => {
    const nodeId = state.sandbox.pipeline_menu_node_id;
    const nodes = state.sandbox.pipeline?.nodes;
    return nodeId === undefined || !nodes || nodes?.length <= 0
      ? null
      : nodes.find((n) => n.id === nodeId) || null;
  });

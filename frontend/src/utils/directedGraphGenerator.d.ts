import { IEdgeData, INodeData } from "../API/pipeline/pipelineInterface";

export declare const runDirectedGraph: (
  container: HTMLDivElement,
  linksData: IEdgeData[],
  nodesData: INodeData[],
  onContextMenuNode: (event: PointerEvent, id: string) => void
  // onContextMenuEdge,
  // onMouseDownNode,
  // onMouseUpNode,
  // onMouseUpSvg
) => {
  destroy: () => void;
  nodes: () => SVGSVGElement | null;
};

import React from "react";
import { runDirectedGraph } from "./directedGraphGenerator";
import styles from "./directedGraph.module.scss";

export type EdgeDataType = {
  source: number;
  target: number;
};
export type NodeDataType = {
  id: number;
  display_name: string;
  model_name: string;
  class: string;
  params: any;
  parents: number[];
  children: number[];
};

type DirectedGraphProps = {
  edgesData: EdgeDataType[];
  nodesData: NodeDataType[];
};
const DirectedGraph = ({ edgesData, nodesData }: DirectedGraphProps) => {
  const containerRef = React.useRef(null);

  React.useEffect((): any => {
    let destroyFn;

    if (containerRef.current) {
      const { destroy } = runDirectedGraph(
        containerRef.current,
        edgesData,
        nodesData
      );
      destroyFn = destroy;
    }

    return destroyFn;
  }, [nodesData, edgesData]);

  return <div ref={containerRef} className={styles.container} />;
};

export default DirectedGraph;

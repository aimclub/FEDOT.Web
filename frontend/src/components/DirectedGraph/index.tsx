import React, { useState } from "react";
import { runDirectedGraph } from "./directedGraphGenerator";
import styles from "./directedGraph.module.scss";
import Loader from "react-loader-spinner";

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
  const [showLoader, setShowLoader] = useState(true);

  React.useEffect((): any => {
    if (edgesData.length === 0 || nodesData.length === 0) return;
    let destroyFn;
    setShowLoader(false);
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

  return (
    <div ref={containerRef} className={styles.container}>
      {showLoader && (
        <Loader
          type="MutatingDots"
          color="#263238"
          secondaryColor="#0199E4"
          height={100}
          width={100}
          timeout={3000}
        />
      )}
    </div>
  );
};

export default DirectedGraph;

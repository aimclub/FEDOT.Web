import React, { useEffect, useState } from "react";
import { runHistory } from "./historyGraphGenerator";
import styles from "./History.module.scss";
import Loader from "react-loader-spinner";
import { IHistoryGraph, sandboxAPI } from "../../api/sandbox";
import { Simulate } from "react-dom/test-utils";

export type HistoryEdgeType = {
  source: string;
  target: string;
};
export type HistoryNodeType = {
  uid: string;
  type: string;
  chain_id?: any;
  full_name?: any;
  objs?: any;
};

type DirectedGraphProps = {
  edgesData: HistoryEdgeType[];
  nodesData: HistoryNodeType[];
  onClick(d: any): void;
};

export type dataContextType = {
  data: number;
};
const History = ({ edgesData, nodesData, onClick }: DirectedGraphProps) => {
  const containerRef = React.useRef(null);
  const [showLoader, setShowLoader] = useState(true);

  React.useEffect((): any => {
    if (edgesData.length === 0 || nodesData.length === 0) return;
    let destroyFn;

    setShowLoader(false);
    if (containerRef.current) {
      const { destroy, nodes } = runHistory(
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
        />
      )}
    </div>
  );
};

export default History;

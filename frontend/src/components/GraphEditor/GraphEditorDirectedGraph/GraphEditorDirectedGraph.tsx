import React, { useState } from "react";
import { runDirectedGraph } from "./directedGraphGenerator";
import styles from "./directedGraph.module.scss";
import Loader from "react-loader-spinner";
import ContextMenu from "../GraphEditorContextMenu/ContextMenu";
import { ClickAwayListener } from "@material-ui/core";

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
  onClickAddNode(d: number): void;
  onClickDeleteNode(d: number): void;
};

type offsetContextMenuType = {
  x: number;
  y: number;
};

export type dataContextType = {
  data: number;
  offset: offsetContextMenuType;
};
const GraphEditorDirectedGraph = ({
  edgesData,
  nodesData,
  onClickAddNode,
  onClickDeleteNode,
}: DirectedGraphProps) => {
  const containerRef = React.useRef(null);
  const [showLoader, setShowLoader] = useState(true);
  const [dataContext, setDataContext] = useState<dataContextType | undefined>(
    undefined
  );

  React.useEffect((): any => {
    if (edgesData.length === 0 || nodesData.length === 0) return;
    let destroyFn;

    const handleContextMenu = (e: any, d: any) => {
      e.preventDefault();
      setDataContext({
        data: d,
        offset: {
          x: e.offsetX,
          y: e.offsetY,
        },
      });
    };

    setShowLoader(false);
    if (containerRef.current) {
      const { destroy } = runDirectedGraph(
        containerRef.current,
        edgesData,
        nodesData,
        handleContextMenu
      );
      destroyFn = destroy;
    }

    return destroyFn;
  }, [nodesData, edgesData]);

  const handleClickAway = () => {
    setDataContext(undefined);
  };

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
      <ClickAwayListener onClickAway={handleClickAway}>
        <div>
          {dataContext && (
            <ContextMenu
              dataContext={dataContext}
              addNode={() => {
                onClickAddNode(dataContext.data);
                setDataContext(undefined);
              }}
              deleteNode={() => {
                onClickDeleteNode(dataContext.data);
                setDataContext(undefined);
              }}
            />
          )}
        </div>
      </ClickAwayListener>
    </div>
  );
};

export default GraphEditorDirectedGraph;

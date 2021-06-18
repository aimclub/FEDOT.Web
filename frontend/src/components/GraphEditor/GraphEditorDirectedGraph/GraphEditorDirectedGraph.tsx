import React, { useEffect, useState } from "react";
import { runDirectedGraph } from "./directedGraphGenerator";
import styles from "./directedGraph.module.scss";
import Loader from "react-loader-spinner";
import ContextMenu from "../GraphEditorContextMenu/ContextMenu";
import { ClickAwayListener } from "@material-ui/core";
import { useDispatch, useSelector } from "react-redux";
import { actionsSandbox } from "../../../store/sandbox-reducer";
import { StateType } from "../../../store/store";
import GraphEditorModal from "../GraphEditorModal/GraphEditorModal";

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

export type offsetContextMenuType = {
  x: number;
  y: number;
};

export type dataContextType = {
  data: number;
  offset: offsetContextMenuType;
};
export type edgeValueType = {
  v: string;
  w: string;
};
export type edgeContextType = {
  data: edgeValueType;
  offset: offsetContextMenuType;
};
const GraphEditorDirectedGraph = ({
  edgesData,
  nodesData,
}: DirectedGraphProps) => {
  const dispatch = useDispatch();
  const containerRef = React.useRef(null);
  const [showLoader, setShowLoader] = useState(true);
  const [dataContext, setDataContext] = useState<dataContextType | undefined>(
    undefined
  );
  const [edgeContext, setEdgeContext] = useState<any>();
  const { mainGraph } = useSelector((state: StateType) => state.sandboxReducer);

  React.useEffect((): any => {
    if (edgesData.length === 0 || nodesData.length === 0) return;
    let destroyFn;

    const handleContextMenuNode = (e: any, d: any) => {
      e.preventDefault();
      setDataContext({
        data: d,
        offset: {
          x: e.offsetX,
          y: e.offsetY,
        },
      });
    };

    const handleContextMenuEdge = (e: any, d: any) => {
      e.preventDefault();
      setEdgeContext({
        data: d,
        offset: {
          x: e.offsetX,
          y: e.offsetY,
        },
      });
      console.log(`### d`, d);
      console.log(`### handleContextMenuEdge`);
    };

    setShowLoader(false);
    if (containerRef.current) {
      const { destroy } = runDirectedGraph(
        containerRef.current,
        edgesData,
        nodesData,
        handleContextMenuNode,
        handleContextMenuEdge
      );
      destroyFn = destroy;
    }

    return destroyFn;
  }, [nodesData, edgesData]);

  const handleClickAwayNodeContext = () => {
    setDataContext(undefined);
  };
  const handleClickAwayEdgeContext = () => {
    setEdgeContext(undefined);
  };

  const handleAddNode = (): void => {
    if (dataContext) {
      //TODO: необходимо создавать уникальный id
      const newNode = {
        ...mainGraph.nodes[0],
        id: 1000 + mainGraph.nodes.length,
      };
      const newEdge = { source: newNode.id, target: Number(dataContext.data) };
      console.log(`### newNode`, newNode);
      console.log(`### newEdge`, newEdge);
      dispatch(
        actionsSandbox.addNodeMainGraph({
          nodes: [newNode],
          edges: [newEdge],
        })
      );
      setDataContext(undefined);
    }
  };

  const handleSecondActionNode = () => {
    dispatch(actionsSandbox.toggleEditModal());
  };

  const handleDeleteEdge = () => {
    console.log(`### handleDelete`);
    dispatch(actionsSandbox.deleteEdgeMainGraph(edgeContext.data));
    setEdgeContext(undefined);
  };

  useEffect(() => {
    console.log(`### dataContext`, dataContext);
  }, [dataContext]);

  useEffect(() => {
    console.log(`### edgeContext`, edgeContext);
  }, [edgeContext]);

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
      <ClickAwayListener onClickAway={handleClickAwayNodeContext}>
        <div>
          {dataContext && (
            <ContextMenu
              firstName={"add node"}
              secondName={"edit"}
              offset={dataContext?.offset}
              firstAction={handleAddNode}
              secondAction={handleSecondActionNode}
            />
          )}
        </div>
      </ClickAwayListener>
      <ClickAwayListener onClickAway={handleClickAwayEdgeContext}>
        <div>
          {edgeContext && (
            <ContextMenu
              firstName={"delete edge"}
              offset={edgeContext?.offset}
              firstAction={handleDeleteEdge}
            />
          )}
        </div>
      </ClickAwayListener>
      <GraphEditorModal dataContext={dataContext} />
    </div>
  );
};

export default GraphEditorDirectedGraph;

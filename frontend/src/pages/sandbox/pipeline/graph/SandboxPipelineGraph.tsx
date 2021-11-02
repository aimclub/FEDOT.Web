import React, { FC, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";

import styles from "./SandboxPipelineGraph.module.scss";

import AppLoader from "../../../../components/UI/loaders/AppLoader";
import { actionsPipeline } from "../../../../redux/pipeline/pipeline-actions";
import { StateType } from "../../../../redux/store";
import { runDirectedGraph } from "../../../../utils/directedGraphGenerator";
import SandboxPipelineMenu from "../menu/SandboxPipelineMenu";

const SandboxPipelineGraph: FC = () => {
  const containerRef = useRef(null);
  const dispatch = useDispatch();
  const { edges, nodes } = useSelector(
    (state: StateType) => state.pipeline.pipeline
  );
  const { isLoadingPipeline } = useSelector(
    (state: StateType) => state.pipeline
  );

  const handleContextMenuNode = (e: any, id: any) => {
    e.preventDefault();

    dispatch(
      actionsPipeline.setMenuOpen({
        nodeId: id as number,
        position: {
          x: e.offsetX,
          y: e.clientY > 350 ? e.offsetY - 140 : e.offsetY,
        },
      })
    );
  };

  useEffect(() => {
    if (!edges || !nodes || nodes?.length === 0 || isLoadingPipeline) return;

    // отрисовка графа
    if (containerRef.current) {
      const { destroy } = runDirectedGraph(
        containerRef.current,
        edges,
        nodes,
        handleContextMenuNode
      );
      return destroy;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges, isLoadingPipeline]);

  return (
    <div ref={containerRef} className={styles.container}>
      {isLoadingPipeline && <AppLoader />}
      {!isLoadingPipeline && !nodes && <p className={styles.empty}>no data</p>}

      <SandboxPipelineMenu />
    </div>
  );
};

export default SandboxPipelineGraph;

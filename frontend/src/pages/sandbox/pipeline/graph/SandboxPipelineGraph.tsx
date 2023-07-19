import scss from "./SandboxPipelineGraph.module.scss";

import { memo, useCallback, useEffect, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "../../../../hooks/redux";
import { setPipelineMenuNode } from "../../../../redux/sandbox/sandboxSlice";
import { runDirectedGraph } from "../../../../utils/directedGraphGenerator";
import SandboxPipelineMenu from "../menu/SandboxPipelineMenu";

const SandboxPipelineGraph = () => {
  const dispatch = useAppDispatch();
  const { pipeline } = useAppSelector((state) => state.sandbox);
  const [menuPos, setMenuPos] = useState<Record<"x" | "y", number> | null>(
    null
  );
  const graphRef = useRef<HTMLDivElement | null>(null);

  const handleCloseMenu = useCallback(() => setMenuPos(null), []);

  useEffect(() => {
    if (!graphRef.current || !pipeline || pipeline.nodes.length < 1) return;

    const handleContextMenuNode = (event: PointerEvent, node_id: string) => {
      event.preventDefault();
      setMenuPos({
        x: event.offsetX,
        y: event.clientY > 350 ? event.offsetY - 140 : event.offsetY,
      });

      dispatch(setPipelineMenuNode(+node_id));
    };

    {
      const { destroy } = runDirectedGraph(
        graphRef.current,
        pipeline.edges,
        pipeline.nodes,
        handleContextMenuNode
      );
      return () => {
        destroy();
        setMenuPos(null);
      };
    }
  }, [dispatch, pipeline]);

  return (
    <div ref={graphRef} className={scss.root}>
      {!pipeline ? (
        <p className={scss.empty}>no data</p>
      ) : (
        <SandboxPipelineMenu pos={menuPos} onClose={handleCloseMenu} />
      )}
    </div>
  );
};

export default memo(SandboxPipelineGraph);

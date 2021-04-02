import React, { useState } from "react";
import { runForceGraph } from "./forceGraphGenerator";
import styles from "./forceGraph.module.scss";
import CustomSlider from "../Slider";

export function ForceGraph({
  edgesData,
  nodesData,
  nodeHoverTooltip,
  onClick,
}) {
  const containerRef = React.useRef(null);
  const [nodes, setNodes] = useState(nodesData);

  React.useEffect(() => {
    let destroyFn;

    if (containerRef.current) {
      const { destroy } = runForceGraph(
        containerRef.current,
        edgesData,
        nodes,
        nodeHoverTooltip,
        onClick
      );
      destroyFn = destroy;
    }

    return destroyFn;
  }, [nodes]);

  const handleSliderChange = (e, v) => {
    let filteredNodes = nodesData.filter((item) => {
      return item.id < v;
    });
    setNodes(filteredNodes);
  };

  return (
    <div ref={containerRef} className={styles.container}>
      <CustomSlider
        valueLabelDisplay="auto"
        aria-label="pretto slider"
        defaultValue={0}
        value={nodes.length}
        color="primary"
        onChange={handleSliderChange}
        min={1}
        max={nodesData.length}
      />
    </div>
  );
}

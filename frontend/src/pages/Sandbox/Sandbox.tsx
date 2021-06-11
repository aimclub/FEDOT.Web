import React, { ChangeEvent, useEffect } from "react";
import clsx from "clsx";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import style from "./sandbox.module.scss";

import DirectedGraph from "../../components/DirectedGraph/DirectedGraph";
import Header from "../../components/Header/Header";
import CustomSlider from "../../components/Slider/Slider";
import { useDispatch, useSelector } from "react-redux";
import { actionsSandbox, getMainGraph } from "../../store/sandbox-reducer";
import { StateType } from "../../store/store";

const Sandbox = () => {
  const dispatch = useDispatch();
  const { mainGraph } = useSelector((state: StateType) => state.sandboxReducer);

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    console.log(`### handleSliderChange`);
  };

  useEffect(() => {
    dispatch(getMainGraph(45454));
  }, [dispatch]);

  const handleAddNode = (d: any): any => {
    const newNode = { ...mainGraph.nodes[0], id: mainGraph.nodes.length };
    const newEdge = { source: newNode.id, target: d };
    console.log(`### newNode`, newNode);
    dispatch(
      actionsSandbox.addNodeMainGraph({
        nodes: [newNode],
        edges: [newEdge],
      })
    );
    console.log(`### handleAddNode d`, d);
  };

  const handleDeleteNode = (d: any): any => {
    dispatch(actionsSandbox.deleteNodeMainGraph(d));
    console.log(`### handleDeleteNode d`, d);
  };

  return (
    <div className={style.root}>
      <Paper className={style.paper} elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <Paper elevation={3} className={clsx(style.paper, style.paperGrow)}>
        {mainGraph && (
          <DirectedGraph
            edgesData={mainGraph.edges}
            nodesData={mainGraph.nodes}
            onClickAddNode={handleAddNode}
            onClickDeleteNode={handleDeleteNode}
          />
        )}
      </Paper>
      <Paper elevation={3} className={style.paper}>
        <div>
          <CustomSlider
            valueLabelDisplay="auto"
            aria-label="Epoha Slider"
            defaultValue={0}
            value={mainGraph.nodes.length}
            color="primary"
            onChange={handleSliderChange}
            min={1}
            max={mainGraph.nodes.length}
          />
        </div>
      </Paper>
      <Paper elevation={3} className={style.paper}>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
        <div>s</div>
      </Paper>
    </div>
  );
};
export default Sandbox;

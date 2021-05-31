import React, { ChangeEvent, useEffect, useState } from "react";
import clsx from "clsx";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import style from "./sandbox.module.scss";

import DirectedGraph from "../../components/DirectedGraph/DirectedGraph";
import Header from "../../components/Header/Header";
import CustomSlider from "../../components/Slider/Slider";
import { IMainGraph, sandboxAPI } from "../../api/sandbox";
import { useDispatch, useSelector } from "react-redux";
import { getMainGraph } from "../../services/sandboxSlice";
import { RootState } from "../../services/store";
// import data from "../../data/data.json";

const Sandbox = () => {
  const dispatch = useDispatch();
  const { mainGraph } = useSelector((state: RootState) => state.sandbox);

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    console.log(`### handleSliderChange`);
  };

  useEffect(() => {
    dispatch(getMainGraph());
  }, []);

  const handleOnClickGraph = (d: any): any => {
    console.log(`### handleOnClickGraph d`, d);
    // setData((state) => {
    //   const id = state.nodes.length;
    //   const newState = {
    //     nodes: [
    //       ...state.nodes,
    //       ...[
    //         {
    //           id: id,
    //           display_name: "NEW",
    //           model_name: "NEW",
    //           class: "model",
    //           params: { n_neighbors: 8 },
    //           parents: [1, 7],
    //           children: [],
    //         },
    //       ],
    //     ],
    //     edges: [
    //       ...state.edges,
    //       ...[
    //         {
    //           source: id,
    //           target: +d,
    //         },
    //       ],
    //     ],
    //   };
    //   console.log(`### newState`, newState);
    //   return newState;
    // });
  };
  return (
    <div className={style.root}>
      <Paper className={style.paper} elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <Paper elevation={3} className={clsx(style.paper, style.paperGrow)}>
        <DirectedGraph
          edgesData={mainGraph.edges}
          nodesData={mainGraph.nodes}
          onClick={handleOnClickGraph}
        />
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

import React, { ChangeEvent, useEffect, useState } from "react";
import clsx from "clsx";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import style from "./sandbox.module.scss";

import DirectedGraph from "../../components/DirectedGraph/DirectedGraph";
import Header from "../../components/Header/Header";
import CustomSlider from "../../components/Slider/Slider";
import { IMainGraph, sandboxAPI } from "../../api/sandbox";
// import data from "../../data/data.json";

const Sandbox = () => {
  const [buildData, setBuildData] = useState<IMainGraph>({
    nodes: [],
    edges: [],
  });
  const [data, setData] = useState<IMainGraph>({
    nodes: [],
    edges: [],
  });

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    console.log(`### handleSliderChange`);
  };

  useEffect(() => {
    const getData = async () => {
      try {
        const res = await sandboxAPI.getMainGraph(54545);
        setData(res);
        setBuildData(res);
      } catch (e) {
        console.log(`### e`, e);
      }
    };
    getData();

    return;
  }, []);

  const handleOnClickGraph = (d: any): any => {
    console.log(`### d`, d);
    setData((state) => {
      const id = state.nodes.length;
      const newState = {
        nodes: [
          ...state.nodes,
          ...[
            {
              id: id,
              display_name: "NEW",
              model_name: "NEW",
              class: "model",
              params: { n_neighbors: 8 },
              parents: [1, 7],
              children: [],
            },
          ],
        ],
        edges: [
          ...state.edges,
          ...[
            {
              source: id,
              target: +d,
            },
          ],
        ],
      };
      console.log(`### newState`, newState);
      return newState;
    });
  };
  return (
    <div className={style.root}>
      <Paper className={style.paper} elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <Paper elevation={3} className={clsx(style.paper, style.paperGrow)}>
        <DirectedGraph
          edgesData={data.edges}
          nodesData={data.nodes}
          onClick={handleOnClickGraph}
        />
      </Paper>
      <Paper elevation={3} className={style.paper}>
        <div>
          <CustomSlider
            valueLabelDisplay="auto"
            aria-label="Epoha Slider"
            defaultValue={0}
            value={data.nodes.length}
            color="primary"
            onChange={handleSliderChange}
            min={1}
            max={buildData.nodes.length}
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

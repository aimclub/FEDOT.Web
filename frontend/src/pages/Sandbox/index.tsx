import React, { ChangeEvent, useEffect, useState } from "react";
import clsx from "clsx";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import style from "./sandbox.module.scss";

import DirectedGraph, { NodeDataType } from "../../components/DirectedGraph";
import Header from "../../components/Header";
import CustomSlider from "../../components/Slider";
import { IMainGraph, sandboxAPI } from "../../api/sandbox";

const Sandbox = () => {
  const [selectedNodes, setSelectedNodes] = useState<NodeDataType[]>([]);
  const [data, setData] = useState<IMainGraph>({
    nodes: [],
    edges: [],
  });

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    let filteredNodes = data.nodes.filter((item) => {
      return item.id < v;
    });
    setSelectedNodes(filteredNodes);
  };

  useEffect(() => {
    const getData = async () => {
      try {
        const res = await sandboxAPI.getMainGraph(54545);
        setData(res);
        setSelectedNodes(res.nodes);
      } catch (e) {
        console.log(`### e`, e);
      }
    };
    getData();
  }, []);

  return (
    <div className={style.root}>
      <Paper className={style.paper} elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <Paper elevation={3} className={clsx(style.paper, style.paperGrow)}>
        <DirectedGraph edgesData={data.edges} nodesData={selectedNodes} />
      </Paper>
      <Paper elevation={3} className={style.paper}>
        <div>
          <CustomSlider
            valueLabelDisplay="auto"
            aria-label="Epoha Slider"
            defaultValue={0}
            value={selectedNodes.length}
            color="primary"
            onChange={handleSliderChange}
            min={1}
            max={data.nodes.length}
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

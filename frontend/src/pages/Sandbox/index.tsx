import React, { ChangeEvent, useState } from "react";
import { Paper } from "@material-ui/core";
import data from "../../data/data.json";
import DirectedGraph from "../../components/DirectedGraph";
import style from "./sandbox.module.scss";
import Header from "../../components/Header";
import TerrainIcon from "@material-ui/icons/Terrain";
import CustomSlider from "../../components/Slider";
import clsx from "clsx";

const Sandbox = () => {
  const [nodes, setNodes] = useState(data.nodes);

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    let filteredNodes = data.nodes.filter((item) => {
      return item.id < v;
    });
    setNodes(filteredNodes);
  };

  return (
    <div className={style.root}>
      <Paper className={style.paper} elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <Paper elevation={3} className={clsx(style.paper, style.paperGrow)}>
        <DirectedGraph edgesData={data.edges} nodesData={nodes} />
      </Paper>
      <Paper elevation={3} className={style.paper}>
        <div>
          <CustomSlider
            valueLabelDisplay="auto"
            aria-label="Epoha Slider"
            defaultValue={0}
            value={nodes.length}
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

import React, { ChangeEvent } from "react";
import { useSelector } from "react-redux";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import { makeStyles } from "@material-ui/core/styles";

import Header from "../../components/Header/Header";
import CustomSlider from "../../components/Slider/Slider";
import { StateType } from "../../store/store";
import GraphEditor from "../../components/GraphEditor/GraphEditor";

const useStyles = makeStyles((theme) => ({
  root: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
}));

const Sandbox = () => {
  const classes = useStyles();
  const { mainGraph } = useSelector((state: StateType) => state.sandboxReducer);

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    console.log(`### handleSliderChange`);
  };

  return (
    <div className={classes.root}>
      <Paper elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <GraphEditor />
      <Paper elevation={3}>
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
      <Paper elevation={3}>
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

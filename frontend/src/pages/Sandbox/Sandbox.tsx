import React, { ChangeEvent, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Paper } from "@material-ui/core";
import TerrainIcon from "@material-ui/icons/Terrain";
import { makeStyles } from "@material-ui/core/styles";

import Header from "../../components/Header/Header";
import CustomSlider from "../../components/Slider/Slider";
import { StateType } from "../../store/store";
import GraphEditor from "../../components/GraphEditor/GraphEditor";
import { getEpoch, getMainGraph } from "../../store/sandbox-reducer";
import { EnumHardcode } from "../../utils/enumHardcode";

const useStyles = makeStyles((theme) => ({
  root: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
}));

const Sandbox = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const [valueEpoch, setValueEpoch] = useState(1);
  const { mainGraph, epochList } = useSelector(
    (state: StateType) => state.sandboxReducer
  );

  const handleSliderChange = (e: ChangeEvent<{}>, v: number | number[]) => {
    if (typeof v === "number") {
      setValueEpoch(v);
      let epoch = epochList.find((item) => item.epoch_num === v);
      if (epoch) {
        dispatch(getMainGraph(epoch.chain_id));
      }
    }
  };
  useEffect(() => {
    dispatch(getEpoch(EnumHardcode.caseId));
  }, [dispatch]);

  const arrayValue = epochList.map((item) => item.epoch_num);

  return (
    <div className={classes.root}>
      <Paper elevation={3}>
        <Header title={"Sandbox"} logo={<TerrainIcon />} />
      </Paper>
      <GraphEditor />
      {mainGraph.nodes && (
        <Paper elevation={3}>
          <div>
            <CustomSlider
              valueLabelDisplay="auto"
              getAriaLabel={(index: number) => `${index}`}
              defaultValue={arrayValue[0]}
              value={valueEpoch}
              color="primary"
              onChange={handleSliderChange}
              min={arrayValue[0]}
              max={arrayValue[arrayValue.length - 1]}
              step={1}
              marks
            />
          </div>
        </Paper>
      )}

      <Paper elevation={3}>
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

import React, {FC, memo} from "react";
import {useDispatch, useSelector} from "react-redux";

import {LinearProgress, Slider, Typography} from "@material-ui/core";
import {makeStyles} from "@material-ui/core/styles";
import TimelineIcon from "@material-ui/icons/Timeline";

import {actionsSandbox, getResult,} from "../../../redux/sandbox/sandbox-actions";
import {StateType} from "../../../redux/store";
import {getPipeline} from "../../../redux/pipeline/pipeline-actions";

const useStyles = makeStyles(() => ({
  root: {
    padding: "8px 20px",
    minHeight: 88,

    borderRadius: 8,
    backgroundColor: "#ffffff",

    display: "flex",
    alignItems: "center",
  },
  icon: {
    height: 24,
    width: 24,
  },
  title: {
    margin: "0 12px",
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 700,
    fontSize: 18,
    lineHeight: "150%",
    letterSpacing: "0.15px",

    color: "#263238",
  },
  content: {
    padding: "0 20px",
    flex: 1,
  },
  progress: {
    width: "100%",
    minHeight: 8,

    borderRadius: 4,
    backgroundColor: "rgba(38, 50, 56, 0.4)",
    "& .MuiLinearProgress-bar": {
      maxWidth: "30%",

      borderRadius: 4,
      backgroundColor: "#263238",
    },
  },
  slider: {
    width: "100%",
    color: "#263238",

    "& .MuiSlider-rail": {
      width: "calc(100% + 8px)",
      height: 8,
      borderRadius: "5em",
    },
    "& .MuiSlider-track": {
      height: 8,
      borderRadius: "5em",
    },
    "& .MuiSlider-mark": {
      marginTop: -1,
      height: 8,
      width: 8,

      backgroundColor: "#ffffff",
      border: "1px solid #000",
      borderRadius: "99em",
    },
    "& .MuiSlider-thumb": {
      marginTop: -8,
      marginLeft: -12,
      height: 24,
      width: 24,

      backgroundColor: "#ffffff",
      border: "2px solid currentColor",
      "&:focus, &:hover, &:active": {
        boxShadow: "inherit",
      },
    },
    "& .MuiSlider-valueLabel": {
      left: "calc(-50% + 4px)",
    },
  },
}));

const SandboxEpoch: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { isLoadingCase, showCase } = useSelector(
    (state: StateType) => state.showCase
  );
  const { isLoadingEpochs, epochs } = useSelector(
    (state: StateType) => state.sandbox
  );

  const valueText = (value: number) => `${value}`;

  const handleChangeEpoch = (
    event: React.ChangeEvent<{}>,
    value: number | number[]
  ) => {
    const selectedEpoch = epochs.find((epoch) => epoch.epoch_num === value)!;

    dispatch(actionsSandbox.selectEpoch(selectedEpoch));
    dispatch(getPipeline(selectedEpoch.individual_id));
    dispatch(getResult(showCase?.case_id!, selectedEpoch.individual_id));
  };

  return (
    <section className={classes.root}>
      <TimelineIcon className={classes.icon} />
      <Typography className={classes.title} component="h2">
        Epoch
      </Typography>
      <div className={classes.content}>
        {isLoadingEpochs || isLoadingCase ? (
          <LinearProgress className={classes.progress} />
        ) : (
          <Slider
            className={classes.slider}
            defaultValue={epochs.length}
            onChange={handleChangeEpoch}
            getAriaValueText={valueText}
            valueLabelDisplay="auto"
            marks
            min={1}
            max={epochs.length}
          />
        )}
      </div>
    </section>
  );
};

export default memo(SandboxEpoch);

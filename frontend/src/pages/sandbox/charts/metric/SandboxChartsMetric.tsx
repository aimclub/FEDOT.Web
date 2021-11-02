import { Paper } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC, memo, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import AppLoader from "../../../../components/UI/loaders/AppLoader";
import { actionsSandbox } from "../../../../redux/sandbox/sandbox-actions";
import { StateType } from "../../../../redux/store";
import SandboxChartsMetricData from "./data/SandboxChartsMetricData";

const useStyles = makeStyles(() => ({
  root: {
    padding: "16px 20px",
  },
  title: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 18,
    lineHeight: "150%",
    letterSpacing: "0.15px",

    color: "#263238",
  },
  content: {
    height: 350,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    position: "relative",
  },
  chart: {
    width: "100%",
    height: "100%",
  },
  empty: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 24,
    lineHeight: "100%",
    textAlign: "center",

    color: "#cfd8dc",
  },
}));

const SandboxChartsMetric: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { showCase } = useSelector((state: StateType) => state.showCase);
  const { isLoadingMetric, metric } = useSelector(
    (state: StateType) => state.sandbox
  );

  useEffect(() => {
    if (showCase) dispatch(actionsSandbox.getMetric(showCase.case_id));
  }, [dispatch, showCase]);

  return (
    <Paper className={classes.root} component="article" elevation={3}>
      <h3 className={classes.title}>Metric</h3>
      <div className={classes.content}>
        {isLoadingMetric ? (
          <AppLoader />
        ) : !!metric ? (
          <div className={classes.chart}>
            <SandboxChartsMetricData />
          </div>
        ) : (
          <p className={classes.empty}>no data</p>
        )}
      </div>
    </Paper>
  );
};

export default memo(SandboxChartsMetric);

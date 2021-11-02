import React, { FC, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Redirect } from "react-router";

import { makeStyles } from "@material-ui/core/styles";

import { StateType } from "../../redux/store";
import { AppRoutesEnum } from "../../routes";
import SandboxCharts from "./charts/SandboxCharts";
import SandboxEpoch from "./epoch/SandboxEpoch";
import SandboxPipeline from "./pipeline/SandboxPipeline";
import { actionsSandbox } from "../../redux/sandbox/sandbox-actions";

const useStyles = makeStyles(() => ({
  root: {
    marginBottom: 40,
    display: "grid",
    gap: 20,
    gridTemplateColumns: "100%",
  },
}));

const SandboxPage: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { showCase } = useSelector((state: StateType) => state.showCase);
  const { pipelineFrom } = useSelector((state: StateType) => state.sandbox);

  useEffect(() => {
    if (showCase && pipelineFrom !== "history") {
      dispatch(actionsSandbox.setPipelineUid(showCase.pipeline_id, "showcase"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch, showCase]);

  return showCase ? (
    <div className={classes.root}>
      <SandboxPipeline />
      <SandboxEpoch />
      <SandboxCharts />
    </div>
  ) : (
    <Redirect to={AppRoutesEnum.SHOWCASE} />
  );
};

export default SandboxPage;

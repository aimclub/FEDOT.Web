import React, { FC, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Redirect } from "react-router";

import { makeStyles } from "@material-ui/core/styles";

import { useAppParams } from "../../hooks/useAppParams";
import { getCase } from "../../redux/sandbox/sandbox-actions";
import { AppRoutesEnum } from "../../routes";
import SandboxCharts from "./charts/SandboxCharts";
import SandboxEpoch from "./epoch/SandboxEpoch";
import SandboxPipeline from "./pipeline/SandboxPipeline";
import { StateType } from "../../redux/store";

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
  const { caseId } = useAppParams();
  const { isFromHistory } = useSelector((state: StateType) => state.pipeline);

  const dispatch = useDispatch();

  useEffect(() => {
    if (!isFromHistory) dispatch(getCase(caseId));
  }, [dispatch, caseId, isFromHistory]);

  return caseId ? (
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

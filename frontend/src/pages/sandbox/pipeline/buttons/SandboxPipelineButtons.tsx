import React, { FC, memo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Button } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import AddIcon from "@material-ui/icons/Add";
import AllInboxIcon from "@material-ui/icons/AllInbox";

import {
  actionsPipeline,
  evaluatePipeline,
} from "../../../../redux/pipeline/pipeline-actions";
import { SandboxPointFormType } from "../../../../redux/pipeline/pipeline-types";
import { StateType } from "../../../../redux/store";

const useStyles = makeStyles(() => ({
  root: {
    position: "absolute",
    top: 10,
    left: 30,
    right: 30,
    zIndex: 2,

    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  button: {
    padding: "2px 4px 2px 0",
    textTransform: "none",

    color: "#263238",

    display: "flex",
    flexDirection: "row",
    alignItems: "center",

    "&:hover": {
      color: "#515b5f",
    },
  },
  icon: {
    width: 18,
    height: 18,

    border: "1px solid",
    borderRadius: 5,
  },
  text: {
    paddingLeft: 8,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "16px",
    letterSpacing: "0.15px",
  },
}));

const SandboxPipelineButtons: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();

  const { pipeline, isLoadingPipeline } = useSelector(
    (state: StateType) => state.pipeline
  );
  const { showCase } = useSelector((state: StateType) => state.showCase);

  const handleEvaluateClick = () => {
    if (showCase) {
      dispatch(
        evaluatePipeline(showCase.pipeline_id, pipeline.nodes, pipeline.edges)
      );
    }
  };

  const handleAddPointClick = () => {
    dispatch(actionsPipeline.closeAllModals());
    setTimeout(() => {
      dispatch(
        actionsPipeline.openPointEdit({ type: SandboxPointFormType.ADD_NEW })
      );
    }, 300);
  };

  return (
    <div className={classes.root}>
      <Button
        onClick={handleEvaluateClick}
        className={classes.button}
        disabled={isLoadingPipeline || !pipeline?.uid}
      >
        <AllInboxIcon className={classes.icon} />
        <span className={classes.text}>Evaluate</span>
      </Button>
      <Button
        onClick={handleAddPointClick}
        className={classes.button}
        disabled={isLoadingPipeline || !pipeline?.uid}
      >
        <AddIcon className={classes.icon} />
        <span className={classes.text}>add Point</span>
      </Button>
    </div>
  );
};

export default memo(SandboxPipelineButtons);

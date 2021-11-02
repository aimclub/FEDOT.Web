import React, { FC, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import { IPipeline } from "../../../API/pipeline/pipelineInterface";
import AppLoader from "../../../components/UI/loaders/AppLoader";
import { actionsPipeline } from "../../../redux/pipeline/pipeline-actions";
import { actionsSandbox } from "../../../redux/sandbox/sandbox-actions";
import { StateType } from "../../../redux/store";
import SandboxPipelineButtons from "./buttons/SandboxPipelineButtons";
import SandboxPipelineGraph from "./graph/SandboxPipelineGraph";
import SandboxPipelineNodeEdit from "./nodeEdit/SandboxPipelineNodeEdit";
import SandboxPipelinePointEdit from "./pointEdit/SandboxPipelinePointEdit";

const useStyles = makeStyles(() => ({
  root: {
    padding: 32,
    height: 522,
    boxSizing: "border-box",

    borderRadius: 8,
    background: "#FFFFFF",

    position: "relative",
  },
  graph: {
    height: "100%",
    overflow: "auto",
  },
}));

const SandboxPipeline: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { showCase } = useSelector((state: StateType) => state.showCase);
  const { caseParams, pipelineUid } = useSelector(
    (state: StateType) => state.sandbox
  );
  const { isEvaluatingPipeline } = useSelector(
    (state: StateType) => state.pipeline
  );

  useEffect(() => {
    if (showCase) {
      dispatch(actionsSandbox.getCaseParams(showCase.case_id));
    }
  }, [dispatch, showCase]);

  useEffect(() => {
    if (caseParams.task_id) {
      dispatch(actionsPipeline.getModelNames(caseParams.task_id));
    }
  }, [dispatch, caseParams]);

  useEffect(() => {
    !!pipelineUid
      ? dispatch(actionsPipeline.getPipeline(pipelineUid))
      : dispatch(actionsPipeline.setPipeline({} as IPipeline));
  }, [dispatch, pipelineUid]);

  return (
    <section className={classes.root}>
      {isEvaluatingPipeline && <AppLoader hasBlackout={true} />}
      <SandboxPipelineButtons />
      <div className={classes.graph}>
        <SandboxPipelineGraph />
      </div>
      <SandboxPipelinePointEdit />
      <SandboxPipelineNodeEdit />
    </section>
  );
};

export default SandboxPipeline;

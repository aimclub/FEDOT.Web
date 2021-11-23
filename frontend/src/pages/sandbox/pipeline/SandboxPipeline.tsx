import React, { FC } from "react";
import { useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import AppLoader from "../../../components/UI/loaders/AppLoader";
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
  const { isEvaluatingPipeline } = useSelector(
    (state: StateType) => state.pipeline
  );

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

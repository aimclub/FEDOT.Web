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
    height: "93%",
    overflow: "auto",
  },
  downloadButton: {
    padding: 12,
    minWidth: 208,
    boxSizing: "border-box",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "150%",
    letterSpacing: "0.15px",
    textTransform: "none",
    textDecoration: "none",
    textAlign: "center",

    color: "#FFFFFF",
    borderRadius: "4px",
    background: "#263238",

    position: "absolute",
    bottom: 24,
    right: 24,

    display: "block",
    "&:hover": {
      background: "#515B5F",
    },
  },
}));

const SandboxPipeline: FC = () => {
  const classes = useStyles();
  const { isEvaluatingPipeline } = useSelector(
    (state: StateType) => state.pipeline
  );

  const { nodes, edges, uid } = useSelector(
    (state: StateType) => state.pipeline.pipeline
  );
  const pipeline = {
    nodes: nodes,
    edges: edges,
    uid: uid,
  };

  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      uid: pipeline.uid,
      pipeline: pipeline,
      overwrite: false,
    }),
  };

  const jsonFileDownload = () => {

    fetch("/download_pipeline", options)
      .then((response) => response.json())
      .then((data) => {
        const jsonString = JSON.stringify(data);
        // Create a Blob from the JSON string
        const blob = new Blob([jsonString], { type: "application/json" });
        // Create a URL for the Blob
        const url = URL.createObjectURL(blob);
        // Create an anchor element and set its properties
        const a = document.createElement("a");
        a.href = url;
        a.download = `pipeline_${Date.now()}.json`; 

        a.click();
        URL.revokeObjectURL(url);
        a.remove();
      })
      .catch((error) => console.error("fetch error: ", error));
  };

  return (
    <section className={classes.root}>
      {isEvaluatingPipeline && <AppLoader hasBlackout={true} />}
      <SandboxPipelineButtons />
      <div className={classes.graph}>
        <SandboxPipelineGraph />
      </div>
      <button className={classes.downloadButton} onClick={jsonFileDownload}>
        Download
      </button>
      <SandboxPipelinePointEdit />

      <SandboxPipelineNodeEdit />
    </section>
  );
};

export default SandboxPipeline;

import scss from "./sandboxPipelineNodeEdges.module.scss";

import { memo, useCallback, useEffect, useRef } from "react";

import Fade from "@mui/material/Fade";
import Paper from "@mui/material/Paper";
import CloseIcon from "@mui/icons-material/Close";

import { useAppDispatch, useAppSelector } from "../../../../hooks/redux";
import IconButton from "@mui/material/IconButton";
import {
  editPipelineNodeEdges,
  setPipelineNodeEdgesType,
} from "../../../../redux/sandbox/sandboxSlice";
import PipelineNodeEdgesForm, {
  IPipelineNodesEdgesValues,
} from "../../../../components/forms/pipelineNode/edges/PipelineNodeEdgesForm";

const SandboxPipelineNodeEdges = () => {
  const dispatch = useAppDispatch();
  const paperRef = useRef<HTMLDivElement | null>(null);
  const { type, node } = useAppSelector(
    (state) => state.sandbox.pipeline_node_edges
  );

  const handleClose = useCallback(() => {
    dispatch(setPipelineNodeEdgesType(null));
  }, [dispatch]);

  const handleSubmit = useCallback(
    (values: IPipelineNodesEdgesValues) => {
      dispatch(editPipelineNodeEdges(values));
      dispatch(setPipelineNodeEdgesType(null));
    },
    [dispatch]
  );

  useEffect(() => {
    // анимация при смене node
    if (type !== null)
      paperRef.current?.animate([{ opacity: 0 }, { opacity: 1 }], 300);
  }, [node, type]);

  return (
    <Fade in={type !== null} mountOnEnter unmountOnExit>
      <Paper className={scss.root} elevation={3} ref={paperRef}>
        <div className={scss.header}>
          <p className={scss.title}>
            {type === "add"
              ? "add Point"
              : type === "edit" && `edit Point id:${node?.id}`}
          </p>
          <IconButton className={scss.close} onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </div>
        <PipelineNodeEdgesForm
          initialValues={node}
          onSubmit={handleSubmit}
          onClose={handleClose}
        />
      </Paper>
    </Fade>
  );
};

export default memo(SandboxPipelineNodeEdges);

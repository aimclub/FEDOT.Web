import scss from "./sandboxPipelineNodeParams.module.scss";

import { memo, useCallback, useEffect, useRef } from "react";

import CloseIcon from "@mui/icons-material/Close";
import Fade from "@mui/material/Fade";
import Paper from "@mui/material/Paper";
import IconButton from "@mui/material/IconButton";

import { INodeData } from "../../../../API/pipeline/pipelineInterface";
import PipelineNodeParamsForm from "../../../../components/forms/pipelineNode/params/PipelineNodeParamsForm";
import { useAppDispatch, useAppSelector } from "../../../../hooks/redux";
import {
  editPipelineNodeParams,
  setPipelineNodeParamsOpen,
} from "../../../../redux/sandbox/sandboxSlice";

const SandboxPipelineNodeParams = () => {
  const dispatch = useAppDispatch();
  const paperRef = useRef<HTMLDivElement | null>(null);
  const { open, node } = useAppSelector(
    (state) => state.sandbox.pipeline_node_params
  );

  const handleClose = useCallback(() => {
    dispatch(setPipelineNodeParamsOpen(false));
  }, [dispatch]);

  const handleSubmit = useCallback(
    (values: INodeData) => {
      dispatch(editPipelineNodeParams(values));
      dispatch(setPipelineNodeParamsOpen(false));
    },
    [dispatch]
  );

  useEffect(() => {
    // анимация при смене node
    if (open) paperRef.current?.animate([{ opacity: 0 }, { opacity: 1 }], 300);
  }, [node, open]);

  return (
    <Fade in={open} mountOnEnter unmountOnExit>
      <Paper className={scss.root} elevation={3} ref={paperRef}>
        <div className={scss.header}>
          <p className={scss.title}>{`XGB | ML ${node?.type}`}</p>
          <IconButton className={scss.close} onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </div>
        <PipelineNodeParamsForm
          initialValues={node}
          onSubmit={handleSubmit}
          onClose={handleClose}
        />
      </Paper>
    </Fade>
  );
};

export default memo(SandboxPipelineNodeParams);

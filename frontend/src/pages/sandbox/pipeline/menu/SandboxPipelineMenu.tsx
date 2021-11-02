import React, { FC } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  Button,
  ClickAwayListener,
  Paper,
  Typography,
} from "@material-ui/core";

import { useStyles } from "./SandboxPipelineMenuStyle";

import { INodeData } from "../../../../API/pipeline/pipelineInterface";
import { actionsPipeline } from "../../../../redux/pipeline/pipeline-actions";
import { StateType } from "../../../../redux/store";
import { SandboxPointFormType } from "../../../../redux/pipeline/pipeline-types";

interface IButton {
  name: string;
  action: () => void;
}

const SandboxPipelineMenu: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { isOpen, position, nodeId } = useSelector(
    (state: StateType) => state.pipeline.menu
  );
  const { nodes } = useSelector((state: StateType) => state.pipeline.pipeline);
  const { nodeEdit, pointEdit } = useSelector(
    (state: StateType) => state.pipeline
  );

  const handleClickAway = () => {
    dispatch(actionsPipeline.setMenuClose());
  };

  const handleEdgesEdit = () => {
    dispatch(actionsPipeline.closeAllModals());

    const node = nodes.find((item) => +(nodeId as number) === item.id);

    setTimeout(() => {
      dispatch(
        actionsPipeline.openPointEdit({
          type: SandboxPointFormType.EDIT,
          node,
        })
      );
    }, 300);
  };

  const handleNodeParamsEdit = () => {
    dispatch(actionsPipeline.closeAllModals());

    const node = nodes.find((item) => +(nodeId as number) === item.id);

    dispatch(actionsPipeline.setNodeEditData(node as INodeData));

    setTimeout(() => {
      dispatch(actionsPipeline.setNodeEditOpen(true));
    }, 300);
  };

  const handleNodeDelete = () => {
    dispatch(actionsPipeline.setMenuClose());
    dispatch(actionsPipeline.deletePipelineNode(nodeId as number));
    console.log(nodeEdit);

    if (nodeEdit.isOpen && nodeEdit.node?.id === +(nodeId as number)) {
      dispatch(actionsPipeline.setNodeEditOpen(false));
    }

    if (pointEdit.isOpen && pointEdit.node?.id === +(nodeId as number)) {
      dispatch(actionsPipeline.closePointEdit());
    }
  };

  const buttons: IButton[] = [
    { name: "edit edges", action: handleEdgesEdit },
    { name: "edit params", action: handleNodeParamsEdit },
    { name: "delete", action: handleNodeDelete },
  ];

  return isOpen ? (
    <ClickAwayListener onClickAway={handleClickAway}>
      <Paper
        className={classes.root}
        style={{ top: `${position.y}px`, left: position.x }}
        elevation={3}
      >
        <Typography className={classes.title}>point menu</Typography>
        <div className={classes.content}>
          {buttons.map((b) => (
            <Button key={b.name} onClick={b.action} className={classes.item}>
              {b.name}
            </Button>
          ))}
        </div>
      </Paper>
    </ClickAwayListener>
  ) : (
    <></>
  );
};

export default SandboxPipelineMenu;

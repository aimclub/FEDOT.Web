import React, { FC } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Button, Fade, IconButton, Paper } from "@material-ui/core";
import CloseIcon from "@material-ui/icons/Close";
import StarRateIcon from "@material-ui/icons/StarRate";

import { useStyles } from "./SandboxPipelineNodeEditStyle";

import AppSelect from "../../../../components/UI/selects/AppSelect";
import { actionsPipeline } from "../../../../redux/pipeline/pipeline-actions";
import { StateType } from "../../../../redux/store";
import SandboxPipelineNodeEditParams from "./params/SandboxPipelineNodeEditParams";

const SandboxPipelineNodeEdit: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { node, isOpen } = useSelector(
    (state: StateType) => state.pipeline.nodeEdit
  );
  const { pipeline } = useSelector((state: StateType) => state.pipeline);
  const { modelNames } = useSelector((state: StateType) => state.sandbox);

  const handleClose = () => {
    dispatch(actionsPipeline.setNodeEditOpen(false));
  };

  const handleDisplayNameChange = (
    event: React.ChangeEvent<{ name?: string | undefined; value: unknown }>
  ) => {
    const displayName = event.target.value as string;
    dispatch(
      actionsPipeline.setNodeEditData({
        ...node,
        display_name: displayName,
        type: modelNames.find((i) => i.display_name === displayName)!.type,
      })
    );
  };

  const handleSubmit = () => {
    dispatch(actionsPipeline.editPipelineNode(pipeline, node, pipeline.edges));
  };

  return (
    <Fade in={isOpen} mountOnEnter unmountOnExit>
      <Paper elevation={3} className={classes.dialog}>
        <div className={classes.header}>
          <p className={classes.title}>{`XGB | ML ${node.type}`}</p>
          <IconButton className={classes.closeButton} onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </div>
        <div className={classes.content}>
          <div className={classes.contentLine}>
            <div className={classes.ratting}>
              <StarRateIcon className={classes.rattingIcon} />
              <p className={classes.text}>{`Rating ${
                node.rating || "?"
              }/10`}</p>
            </div>
            <p className={classes.text}>{`id: ${node.id}`}</p>
          </div>

          <div className={classes.contentLine}>
            <p className={classes.text}>Display_name: </p>
            <AppSelect
              classname={classes.value}
              name="displayName"
              currentValue={node.display_name}
              availableValues={modelNames.map((n) => ({
                id: n.display_name,
                name: n.display_name,
              }))}
              onChange={handleDisplayNameChange}
            />
          </div>

          <SandboxPipelineNodeEditParams />

          <div className={classes.buttonGroup}>
            <Button
              className={`${classes.button} ${classes.cancelButton}`}
              onClick={handleClose}
            >
              cancel
            </Button>
            <Button
              className={`${classes.button} ${classes.submitButton}`}
              onClick={handleSubmit}
            >
              apply
            </Button>
          </div>
        </div>
      </Paper>
    </Fade>
  );
};

export default SandboxPipelineNodeEdit;

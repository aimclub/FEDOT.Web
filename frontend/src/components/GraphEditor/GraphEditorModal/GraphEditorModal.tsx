import React, { FC, useEffect, useState } from "react";
import {
  Button,
  Dialog,
  Input,
  Modal,
  Paper,
  Slide,
  Typography,
} from "@material-ui/core";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../../store/store";
import { actionsSandbox } from "../../../store/sandbox-reducer";
import { makeStyles } from "@material-ui/core/styles";
import { TransitionProps } from "@material-ui/core/transitions";

const useStyles = makeStyles((theme) => ({
  root: {
    width: 278,
    position: "absolute",
    right: 50,
    top: "40%",
    transform: "translate(0, -50%)",
  },
  paperGrow: {
    flexGrow: 1,
    display: "flex",
  },
}));

const Transition = React.forwardRef(function Transition(
  props: TransitionProps & { children?: React.ReactElement<any, any> },
  ref: React.Ref<unknown>
) {
  return <Slide direction="left" ref={ref} {...props} />;
});

interface IGraphEditorModal {}

const GraphEditorModal: FC<IGraphEditorModal> = (props) => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { isOpenEditModal } = useSelector(
    (state: StateType) => state.sandboxReducer
  );
  const handleClose = () => {
    dispatch(actionsSandbox.toggleEditModal());
  };
  useEffect(() => {
    console.log(`### isOpenEditModal`, isOpenEditModal);
  }, [isOpenEditModal]);

  return (
    <Dialog
      hideBackdrop
      open={isOpenEditModal}
      TransitionComponent={Transition}
      onClose={handleClose}
      aria-labelledby="edit-modal-title"
      aria-describedby="edit-modal-description"
    >
      <Paper className={classes.root}>
        <Typography>XGB | ML model</Typography>
        <div>
          <Typography>Rating 10/10</Typography>
          <div>
            <Typography>Display_name</Typography>
            <Input />
          </div>
          <Typography>Hyperparameters</Typography>
          <div>{/*  table hyperparameters*/}</div>
          <div>
            <Typography>NameParam</Typography>
            <Input />
            <Button>add</Button>
          </div>
          <Typography>Custom hyperparameters</Typography>
          <div>{/* table custom hyperparameters*/}</div>
        </div>
        <Button>cancel</Button>
        <Button>delete</Button>
      </Paper>
    </Dialog>
  );
};
export default GraphEditorModal;

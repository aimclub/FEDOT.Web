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
  dialog: {
    position: "absolute",
    top: "40%",
    right: "50px",
    transform: "translate(0, -50%)",
  },
  root: {
    width: 278,
  },
  paperGrow: {
    flexGrow: 1,
    display: "flex",
  },
  title: {
    backgroundColor: "#B0BEC5",
    padding: "6px 12px",
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
      classes={{
        paper: classes.dialog,
      }}
    >
      <Paper className={classes.root}>
        <Typography className={classes.title} variant={"subtitle1"}>
          XGB | ML model
        </Typography>
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

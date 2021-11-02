import React, { FC } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useHistory } from "react-router-dom";

import { Button, Dialog, IconButton } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import CloseIcon from "@material-ui/icons/Close";

import { staticAPI } from "../../../API/baseURL";
import AppLoader from "../../../components/UI/loaders/AppLoader";
import { closeHistoryModal } from "../../../redux/history/history-actions";
import { actionsSandbox } from "../../../redux/sandbox/sandbox-actions";
import { StateType } from "../../../redux/store";
import { AppRoutesEnum } from "../../../routes";

const useStyles = makeStyles(() => ({
  header: {
    margin: 2,
    padding: 8,

    borderRadius: 20,
    background: "#E2E7EA",

    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "20px",
    letterSpacing: "0.25px",

    color: "#263238",
  },
  closeButton: {
    padding: 2,

    color: "#263238",
  },
  content: {
    minWidth: 200,
    minHeight: 200,

    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  image: {
    height: "100%",
    width: "100%",

    objectFit: "contain",
    objectPosition: "center",
  },
  buttons: {
    padding: 8,

    display: "grid",
    gap: 20,
    gridAutoFlow: "column",
    justifyContent: "flex-end",
  },
  empty: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 24,
    lineHeight: "100%",
    textAlign: "center",

    color: "#cfd8dc",
  },
}));

const HistoryModal: FC = () => {
  const classes = useStyles();
  const history = useHistory();
  const dispatch = useDispatch();
  const { isOpen, pipeline, pipelineImage, isLoadingPipelineImage } =
    useSelector((state: StateType) => state.history.modal);

  const handleClose = () => {
    if (isLoadingPipelineImage) return;
    dispatch(closeHistoryModal());
  };

  const handleEditPipeline = () => {
    if (pipelineImage?.uid) {
      dispatch(actionsSandbox.setPipelineUid(pipelineImage.uid, "history"));
      history.push(AppRoutesEnum.SANDBOX);

      handleClose();
    }
  };

  return (
    <Dialog open={isOpen} onClose={handleClose}>
      <div className={classes.header}>
        <p>{pipeline?.uid}</p>
        <IconButton onClick={handleClose} className={classes.closeButton}>
          <CloseIcon />
        </IconButton>
      </div>
      <div className={classes.content}>
        {isLoadingPipelineImage ? (
          <AppLoader />
        ) : !!pipelineImage ? (
          <img
            className={classes.image}
            src={staticAPI.getImage(pipelineImage.image_url)}
            alt={pipeline?.uid}
          />
        ) : (
          <p className={classes.empty}>no data</p>
        )}
      </div>
      <div className={classes.buttons}>
        <Button size={"small"} onClick={handleClose} color="primary">
          cancel
        </Button>
        <Button
          size={"small"}
          onClick={handleEditPipeline}
          variant={"contained"}
          disabled={!pipelineImage || isLoadingPipelineImage}
        >
          edit
        </Button>
      </div>
    </Dialog>
  );
};

export default HistoryModal;

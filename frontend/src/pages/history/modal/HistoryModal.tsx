import React, { FC } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useHistory } from "react-router-dom";

import { Button, Dialog, IconButton } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import CloseIcon from "@material-ui/icons/Close";

import { staticAPI } from "../../../API/baseURL";
import AppLoader from "../../../components/UI/loaders/AppLoader";
import { closeHistoryModal } from "../../../redux/history/history-actions";
import { getResult } from "../../../redux/sandbox/sandbox-actions";
import { StateType } from "../../../redux/store";
import { AppRoutesEnum } from "../../../routes";
import {
  actionsPipeline,
  getPipeline,
} from "../../../redux/pipeline/pipeline-actions";
import { useAppParams } from "../../../hooks/useAppParams";

const useStyles = makeStyles(() => ({
  header: {
    margin: 0,
    padding: "6px 12px",

    background: "#B0BEC5",

    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  title: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "22px",

    color: "#4f4f4f",
  },
  closeButton: {
    padding: 2,
  },
  content: {
    padding: 14,

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
  buttonGroup: {
    margin: "0 14px 20px 0",

    display: "flex",
    justifyContent: "flex-end",
    alignItems: "center",
  },
  button: {
    padding: "4px 16px",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "24px",
    letterSpacing: "0.1px",
    textTransform: "uppercase",

    borderRadius: 4,
  },
  cancelButton: {
    color: "#828282",
    background: "#F4F5F6",
    "&:hover": {
      background: "#CFD8DC",
    },
  },
  submitButton: {
    marginLeft: 20,
    color: "#ffffff",
    background: "#828282",

    "&:disabled": {
      opacity: 0.5,
      background: "#ECEFF1",
    },
    "&:hover": {
      background: "#515B5F",
    },
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
  const { caseId } = useAppParams();
  const dispatch = useDispatch();
  const { isOpen, pipeline, pipelineImage, isLoadingPipelineImage } =
    useSelector((state: StateType) => state.history.modal);

  const handleClose = () => {
    if (isLoadingPipelineImage) return;
    dispatch(closeHistoryModal());
  };

  const handleEditPipeline = () => {
    if (pipelineImage?.uid) {
      dispatch(actionsPipeline.setPipelineFromHistory(true));
      dispatch(getPipeline(pipelineImage.uid, true));
      dispatch(getResult(caseId, pipelineImage.uid));
      history.push(`${AppRoutesEnum.TO_SANDBOX}${caseId}`);
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
      <div className={classes.buttonGroup}>
        <Button
          className={`${classes.button} ${classes.cancelButton}`}
          onClick={handleClose}
        >
          cancel
        </Button>
        <Button
          className={`${classes.button} ${classes.submitButton}`}
          onClick={handleEditPipeline}
          disabled={!pipelineImage || isLoadingPipelineImage}
        >
          edit
        </Button>
      </div>
    </Dialog>
  );
};

export default HistoryModal;

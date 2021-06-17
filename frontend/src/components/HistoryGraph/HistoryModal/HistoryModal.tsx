import React, { FC, useEffect, useState } from "react";
import {
  createStyles,
  makeStyles,
  Theme,
  withStyles,
  WithStyles,
} from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import MuiDialogTitle from "@material-ui/core/DialogTitle";
import MuiDialogContent from "@material-ui/core/DialogContent";
import MuiDialogActions from "@material-ui/core/DialogActions";
import IconButton from "@material-ui/core/IconButton";
import CloseIcon from "@material-ui/icons/Close";
import Typography from "@material-ui/core/Typography";
import { IChainImage, sandboxAPI } from "../../../api/sandbox";
import Loader from "react-loader-spinner";
import { useHistory } from "react-router-dom";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      padding: theme.spacing(0),
      background: "#E2E7EA",
      borderRadius: "20px",
      margin: 2,
      display: "flex",
      justifyContent: "space-between",
    },
    closeButton: {
      color: theme.palette.grey[500],
      padding: 2,
    },
  });

export interface DialogTitleProps extends WithStyles<typeof styles> {
  id: string;
  children: React.ReactNode;
  onClose: () => void;
}

const DialogTitle = withStyles(styles)((props: DialogTitleProps) => {
  const { children, classes, onClose, ...other } = props;

  return (
    <MuiDialogTitle disableTypography className={classes.root} {...other}>
      <Typography variant="subtitle1">{children}</Typography>
      {onClose ? (
        <IconButton
          aria-label="close"
          className={classes.closeButton}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      ) : null}
    </MuiDialogTitle>
  );
});

const DialogActions = withStyles((theme: Theme) => ({
  root: {
    margin: 0,
    padding: theme.spacing(1),
  },
}))(MuiDialogActions);

interface IHistoryModal {
  handleClose: () => void;
  uid: string;
}

const useStyles = makeStyles((theme) => ({
  paper: {
    background: "#F4F5F6",
  },
  paperInvisible: {
    background: "transparent",
  },
}));

const HistoryModal: FC<IHistoryModal> = ({ handleClose, uid }) => {
  const history = useHistory();

  const classes = useStyles();
  const [showLoader, setShowLoader] = useState(true);
  const [value, setValue] = useState<IChainImage>({} as IChainImage);

  useEffect(() => {
    const getChainsImage = async () => {
      try {
        const res = await sandboxAPI.getChainsImage(uid);
        setValue(res);
        setShowLoader(false);
      } catch (err) {
        setShowLoader(false);
        console.log(err);
      }
    };
    getChainsImage();
  }, []);

  useEffect(() => {
    console.log(`### value`, value);
  }, [value]);

  return (
    <Dialog
      classes={{ paper: showLoader ? classes.paperInvisible : classes.paper }}
      onClose={handleClose}
      aria-labelledby="history-dialog"
      open={Boolean(uid)}
    >
      {showLoader ? (
        <Loader
          type="MutatingDots"
          color="#263238"
          secondaryColor="#0199E4"
          height={100}
          width={100}
        />
      ) : (
        <>
          <DialogTitle id="history-dialog-title" onClose={handleClose}>
            {value.uid}
          </DialogTitle>

          <img src={value.image_url} alt={uid} />
          <DialogActions>
            <Button size={"small"} onClick={handleClose} color="primary">
              cancel
            </Button>
            <Button
              size={"small"}
              onClick={() => {
                history.replace({ pathname: `/sandbox/${value.uid}` });
                handleClose();
              }}
              variant={"contained"}
            >
              edit
            </Button>
          </DialogActions>
        </>
      )}
    </Dialog>
  );
};

export default HistoryModal;

import React, { FC } from "react";
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

const DialogContent = withStyles((theme: Theme) => ({
  root: {
    padding: theme.spacing(2),
  },
}))(MuiDialogContent);

const DialogActions = withStyles((theme: Theme) => ({
  root: {
    margin: 0,
    padding: theme.spacing(1),
  },
}))(MuiDialogActions);

interface IHistoryModal {
  open: boolean;
  handleClose: () => void;
}

const useStyles = makeStyles((theme) => ({
  paper: {
    background: "#F4F5F6",
  },
}));

const HistoryModal: FC<IHistoryModal> = ({ open, handleClose }) => {
  const classes = useStyles();
  return (
    <Dialog
      classes={{ paper: classes.paper }}
      onClose={handleClose}
      aria-labelledby="history-dialog"
      open={open}
    >
      <DialogTitle id="history-dialog-title" onClose={handleClose}>
        Modal title
      </DialogTitle>
      <DialogContent dividers>
        <Typography gutterBottom>
          Cras mattis consectetur purus sit amet fermentum. Cras justo odio,
          dapibus ac facilisis in, egestas eget quam. Morbi leo risus, porta ac
          consectetur ac, vestibulum at eros.
        </Typography>
        <Typography gutterBottom>
          Praesent commodo cursus magna, vel scelerisque nisl consectetur et.
          Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor.
        </Typography>
        <Typography gutterBottom>
          Aenean lacinia bibendum nulla sed consectetur. Praesent commodo cursus
          magna, vel scelerisque nisl consectetur et. Donec sed odio dui. Donec
          ullamcorper nulla non metus auctor fringilla.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button size={"small"} onClick={handleClose} color="primary">
          cancel
        </Button>
        <Button
          size={"small"}
          autoFocus
          onClick={handleClose}
          variant={"contained"}
        >
          edit
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default HistoryModal;

import { makeStyles } from "@material-ui/core/styles";

export const useStyles = makeStyles(() => ({
  dialog: {
    width: 278,

    borderRadius: 4,
    overflow: "hidden",

    position: "absolute",
    top: 30,
    right: 30,
    zIndex: 3,
  },
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
  },
  contentLine: {
    margin: "0 0 15px",

    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 10,
    alignItems: "end",
  },
  text: {
    margin: 0,

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "120%",

    color: "#3D484D",
  },
  value: {},
  buttonGroup: {
    margin: "20px 0 0",

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
      background: "#ECEFF1",
    },
    "&:hover": {
      background: "#515B5F",
    },
  },
  error: {
    color: "#ff0000",
  }
}));

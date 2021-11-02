import { makeStyles } from "@material-ui/core/styles";

export const useStyles = makeStyles(() => ({
  root: {
    position: "absolute",
    top: 0,
    left: 0,
    zIndex: 5,

    borderRadius: 4,
    overflow: "hidden",

    display: "flex",
    flexDirection: "column",
  },
  title: {
    padding: "6px 12px",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "22px",

    color: "#4f4f4f",
    background: "#b0bec5",
  },
  content: {
    padding: 12,

    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "stetch",
  },
  item: {
    marginTop: 4,
    padding: "0 8px",
    width: "100%",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: "normal",
    fontSize: 14,
    lineHeight: "24px",
    letterSpacing: "0.1px",
    textTransform: "none",

    color: "#ffffff",
    borderRadius: 4,
    background: "#828282",

    "&:disabled": {
      background: "#ECEFF1",
    },
    "&:hover": {
      background: "#515B5F",
    },
  },
}));

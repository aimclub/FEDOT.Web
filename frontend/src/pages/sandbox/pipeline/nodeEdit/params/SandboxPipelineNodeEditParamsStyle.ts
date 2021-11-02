import { makeStyles } from "@material-ui/core/styles";

export const useStyles = makeStyles(() => ({
  title: {
    margin: 0,

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "120%",

    color: "#3D484D",
  },
  content: {
    margin: "8px 0",
    padding: "0 6px 6px",
    height: 120,

    borderRadius: 4,
    backgroundColor: "#F4F6F8",

    overflow: "auto",
    position: "relative",

    "&::-webkit-scrollbar": {
      width: 4,
    },
    "&::-webkit-scrollbar-track": {
      boxShadow: "inset 0 0 6px #263238",
      "-webkit-box-shadow": "inset 0 0 6px rgba(34, 60, 80, 0.2)",
      backgroundColor: "#CFD8DC",
      borderRadius: "0 4px 4px  0",
    },
    "&::-webkit-scrollbar-thumb": {
      borderRadius: 4,
      backgroundColor: "#546E7A",
    },
  },
  header: {
    padding: "6px 0 10px",

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 14,
    lineHeight: "120%",
    letterSpacing: "0.25px",

    color: "#506072",
    backgroundColor: "#F4F6F8",

    position: "sticky",
    top: 0,
    zIndex: 1,
  },
  paramLine: {
    margin: "8px 0",

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 14,
    lineHeight: "120%",
    letterSpacing: "0.25px",

    color: "#3D484D",
    alignItems: "center",
  },
  paramName: {
    textOverflow: "ellipsis",
    overflow: "hidden",
  },
  deleteParam: {
    padding: 0,
  },
  deleteParamIcon: {
    width: 15,
    height: 15,
  },
  empty: {
    margin: 0,
    paddingTop: 6,

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "120%",

    color: "#3D484D",
  },
  addParamForm: {
    display: "flex",
    alignItems: "center",
  },
  addParamInput: {
    margin: "0 10px",
    flex: 1,
  },
  addParamLabel: {
    margin: 0,

    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "120%",

    color: "#3D484D",
  },
  buttonAdd: {
    padding: "2px 4px 2px 0",
    textTransform: "none",

    color: "#263238",

    display: "flex",
    flexDirection: "row",
    alignItems: "center",

    "&:hover": {
      color: "#515b5f",
    },
  },
  buttonIcon: {
    width: 18,
    height: 18,

    border: "1px solid",
    borderRadius: 5,
  },
  buttonText: {
    paddingLeft: 8,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "16px",
    letterSpacing: "0.15px",
  },
}));

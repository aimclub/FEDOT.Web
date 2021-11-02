import { makeStyles } from "@material-ui/core/styles";

import Logo from "../../images/Logo.png";

export const useStyles = makeStyles(() => ({
  root: {
    minHeight: "100vh",

    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  },
  logo: {
    marginBottom: 25,
    width: 333,
    height: 57,

    backgroundImage: `url(${Logo})`,
    backgroundSize: "contain",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
  },
  paper: {
    margin: "0 10px",
    padding: "30px 55px 50px",
    width: "calc(100% - 20px)",
    maxWidth: 566,
    boxSizing: "border-box",

    position: "relative",
  },
  loader: {
    width: "100%",
    height: "100%",

    borderRadius: 4,
    backgroundColor: "rgba(0, 0, 0, 0.5)",

    position: "absolute",
    top: 0,
    left: 0,
    zIndex: 1000,

    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    marginBottom: 24,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 24,
    lineHeight: "120%",
    letterSpacing: "0.1px",

    color: "#000000",
  },
  foot: {
    marginTop: 40,

    display: "flex",
    alignItems: "centr",
    justifyContent: "space-between",
  },
  footItem: {
    padding: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "120%",
    letterSpacing: "0.1px",
    textTransform: "none",

    color: "#000000",
    transition: "all 0.5s ease-in-outt",
    "&:hover": {
      color: "#b0bec5",
      background: "transparent",
      cursor: "pointer",
    },
  },
}));

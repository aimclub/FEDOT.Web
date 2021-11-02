import { makeStyles } from "@material-ui/core/styles";

export const useStyles = makeStyles(() => ({
  root: {
    padding: 24,

    borderRadius: 8,
    backgroundColor: "#ffffff",
  },
  content: {
    marginTop: 24,
    padding: "16px 12px",

    borderRadius: 8,
    background: "#e1e2e1",
  },
  title: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 18,
    lineHeight: "150%",
    letterSpacing: "0.15px",

    color: "#000000",
  },
  image: {
    width: "100%",
    height: 182,
    boxSizing: "border-box",

    borderRadius: "8px 0px 0px 8px",
    border: "8px solid #ffffff",
    background: "#ffffff",

    objectFit: "contain",
    objectPosition: "center",
  },
  details: {
    padding: 8,
    height: 182,
    boxSizing: "border-box",

    background: "#ffffff",
    borderRadius: "0px 8px 8px 0px",

    overflow: "hidden",
    overflowY: "auto",

    "&::-webkit-scrollbar": {
      width: 6,
    },
    "&::-webkit-scrollbar-track": {
      boxShadow: "inset 0 0 6px #263238",
      "-webkit-box-shadow": "inset 0 0 6px rgba(34, 60, 80, 0.2)",
      backgroundColor: "#a6acb0",
      borderRadius: 10,
    },
    "&::-webkit-scrollbar-thumb": {
      borderRadius: 10,
      backgroundColor: "#263238",
    },
  },

  metric: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 14,
    lineHeight: "150%",
    letterSpacing: "0.15px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",

    color: "#263238",
  },
  value: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "150%",
    textAlign: "right",
    letterSpacing: "0.15px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",

    color: "#263238",
  },
  description: {
    fontFamily: "'Roboto'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 14,
    lineHeight: "19px",
    letterSpacing: "0.1px",

    color: "#000000",
  },
  item: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
  },
  link: {
    margin: 0,
    padding: "6px 8px",

    fontFamily: "'Open Sans'",
    fontWeight: 300,
    fontSize: "14px",
    lineHeight: "24px",
    letterSpacing: "0.1px",
    textTransform: "none",
    textDecoration: "none",

    color: "#000000",
    borderRadius: 4,
    backgroundColor: "#F5F5F6",
    display: "block",
    "&:hover": {
      background: "#90A4AE",
    },
  },
}));

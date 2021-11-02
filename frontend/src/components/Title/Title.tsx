import { Typography } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC } from "react";

const useStyles = makeStyles(() => ({
  root: {
    minHeight: 42,

    borderBottom: "1px solid #c4c4c4",
  },
  title: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 700,
    fontSize: 18,
    lineHeight: "150%",
    letterSpacing: "0.15px",

    color: "#263238",
  },
}));

interface I {
  name: string;
  type?: "h1" | "h2" | "h3" | "p";
}

const Title: FC<I> = ({ name, type = "p" }) => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Typography className={classes.title} component={type}>
        {name}
      </Typography>
    </div>
  );
};

export default Title;

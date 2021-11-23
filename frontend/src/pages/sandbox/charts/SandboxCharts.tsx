import React, { FC } from "react";
import { Link, useRouteMatch } from "react-router-dom";

import { Grid } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

import { AppRoutesEnum } from "../../../routes";
import SandboxChartsMetric from "./metric/SandboxChartsMetric";
import SandboxChartsResult from "./result/SandboxChartsResult";

const useStyles = makeStyles(() => ({
  root: {
    padding: 24,

    borderRadius: 8,
    background: "#ffffff",
  },
  btns: {
    marginBottom: 24,

    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
  },
  link: {
    padding: 12,
    minWidth: 208,
    boxSizing: "border-box",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "150%",
    letterSpacing: "0.15px",
    textTransform: "none",
    textDecoration: "none",
    textAlign: "center",

    color: "#FFFFFF",
    borderRadius: "4px",
    background: "#263238",

    display: "block",
    "&:hover": {
      background: "#515B5F",
    },
  },
}));

const SandboxCharts: FC = () => {
  const classes = useStyles();
  const { url } = useRouteMatch();

  return (
    <section className={classes.root}>
      <div className={classes.btns}>
        <Link to={`${url}${AppRoutesEnum.TO_HISTORY}`} className={classes.link}>
          History
        </Link>
      </div>
      <Grid container alignContent="flex-end" spacing={2}>
        <Grid item xs={6}>
          <SandboxChartsResult />
        </Grid>
        <Grid item xs={6}>
          <SandboxChartsMetric />
        </Grid>
      </Grid>
    </section>
  );
};

export default SandboxCharts;

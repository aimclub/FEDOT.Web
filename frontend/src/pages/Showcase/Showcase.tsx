import React, { ChangeEvent, useEffect, useState } from "react";
import clsx from "clsx";
import { Grid, Paper } from "@material-ui/core";

import Header from "../../components/Header/Header";
import GradientIcon from "@material-ui/icons/Gradient";
import ShowcaseCard from "../../components/ShowcaseCard/ShowcaseCard";
import { makeStyles } from "@material-ui/core/styles";
// import data from "../../data/data.json";

const useStyles = makeStyles((theme) => ({
  cardList: {
    padding: theme.spacing(3),
  },
}));

const Showcase = () => {
  const classes = useStyles();
  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Header title={"Showcase"} logo={<GradientIcon />} />
      </Grid>

      <Grid container item>
        <Paper className={classes.cardList} elevation={3}>
          <Grid container item spacing={6} justify="center">
            {[...Array(18)].map((item, index) => (
              <Grid key={index} item xs={4}>
                <ShowcaseCard />
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>

      {/*<Paper elevation={3}>sss s s s s</Paper>*/}
    </Grid>
  );
};
export default Showcase;

import React, { FC, memo } from "react";
import { useSelector } from "react-redux";
import { Link } from "react-router-dom";

import { Fade, Grid, Typography } from "@material-ui/core";

import { useStyles } from "./ShowcaseInfoStyle";

import { staticAPI } from "../../../API/baseURL";
import Title from "../../../components/Title/Title";
import CustomTooltip from "../../../components/UI/tooltip/CustomTooltip";
import { StateType } from "../../../redux/store";
import { AppRoutesEnum } from "../../../routes";

const ShowcaseInfo: FC = () => {
  const classes = useStyles();

  const { showCase, isLoadingCase } = useSelector(
    (state: StateType) => state.showCase
  );

  return !isLoadingCase ? (
    <Fade in={showCase !== null} mountOnEnter unmountOnExit timeout={1000}>
      <section className={classes.root}>
        <Title type="h2" name={showCase?.title || ""} />
        <div className={classes.content}>
          <Grid container spacing={2}>
            <Grid item xs={9}>
              <Typography className={classes.title}>Model structure</Typography>
            </Grid>
            <Grid item xs={3}>
              <Typography className={classes.title}>Model details</Typography>
            </Grid>
            <Grid item xs={9}>
              <img
                src={staticAPI.getImage(showCase?.icon_path || "")}
                alt={showCase?.title}
                className={classes.image}
              />
            </Grid>
            <Grid item xs={3}>
              <div className={classes.details}>
                {Object.entries(showCase?.details as object).map((metric) => (
                  <CustomTooltip
                    key={metric[0]}
                    title={`${metric[0]}: ${metric[1]}`}
                    placement="top"
                    arrow
                  >
                    <Grid container spacing={2}>
                      <Grid item xs={8}>
                        <Typography className={classes.metric}>
                          {metric[0]}
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography className={classes.value}>
                          {metric[1]}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CustomTooltip>
                ))}
              </div>
            </Grid>
            <Grid item xs={12}>
              <Typography className={classes.description}>
                {showCase?.description}
              </Typography>
            </Grid>
            <Grid item xs={12} className={classes.item}>
              <Link to={AppRoutesEnum.SANDBOX} className={classes.link}>
                Edit in Sandbox
              </Link>
            </Grid>
          </Grid>
        </div>
      </section>
    </Fade>
  ) : (
    <div></div>
  );
};

export default memo(ShowcaseInfo);

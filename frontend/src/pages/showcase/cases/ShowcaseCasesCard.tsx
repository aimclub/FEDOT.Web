import React, { FC, memo } from "react";
import { useDispatch } from "react-redux";

import { Button, Typography } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

import { staticAPI } from "../../../API/baseURL";
import { ICaseItem } from "../../../API/showcase/showcaseInterface";
import { getShowCase } from "../../../redux/showCase/showCase-actions";

const useStyles = makeStyles(() => ({
  root: {
    padding: 8,
    width: 370,

    borderRadius: 8,
    backgroundColor: "#e0e0e0",
  },
  image: {
    width: "100%",
    height: 110,

    borderRadius: 8,
    // objectFit: "cover",
    // objectPosition: "center",
  },
  caption: {
    marginTop: 4,

    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    margin: 0,

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "150%",
    letterSpacing: "0.15px",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
    overflow: "hidden",

    color: "#263238",
  },
  button: {
    padding: 4,

    fontFamily: "Open Sans",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "24px",
    letterSpacing: "0.1px",
    textTransform: "none",

    color: "#FFFFFF",
    background: "#1A2327",
    "&:hover": {
      background: "#515B5F",
    },
  },
}));

interface I {
  data: ICaseItem;
}

const ShowcaseCasesCard: FC<I> = ({ data }) => {
  const classes = useStyles();

  const dispatch = useDispatch();

  const handleCaseExpand = () => {
    dispatch(getShowCase(data.case_id));
  };

  return (
    <article className={classes.root}>
      <img
        src={staticAPI.getImage(data.icon_path)}
        alt={data.title}
        className={classes.image}
      />
      <div className={classes.caption}>
        <Typography className={classes.title} component="h3">
          {data.title}
        </Typography>
        <Button className={classes.button} onClick={handleCaseExpand}>
          Expand
        </Button>
      </div>
    </article>
  );
};

export default memo(ShowcaseCasesCard);

import React, { FC } from "react";
import { Button, Paper, Typography } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import cardImg from "../../assets/images/card.png";

interface IShowcaseCard {}

const useStyles = makeStyles((theme) => ({
  root: {
    maxWidth: 386,
    backgroundColor: "#E0E0E0",
  },
  img: {},
  button: {},
}));

const ShowcaseCard: FC<IShowcaseCard> = (props) => {
  const classes = useStyles();
  return (
    <Paper className={classes.root}>
      <img src={cardImg} alt="card" />
      <Typography variant={"caption"}>Case name</Typography>
      <Button>Expand</Button>
    </Paper>
  );
};
export default ShowcaseCard;

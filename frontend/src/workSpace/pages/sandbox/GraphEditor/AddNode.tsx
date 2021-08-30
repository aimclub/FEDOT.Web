import React, { memo, useCallback, useState } from "react";

import { makeStyles, createStyles } from "@material-ui/core/styles";

import AddButton from "../../../../ui/buttons/AddButton";
import AddNodeForm from "../../../components/forms/addNode/AddNodeForm";
import { Fade } from "@material-ui/core";

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      position: "relative",
    },
    button: {
      position: "absolute",
      top: -25,
      right: 0,
      zIndex: 2,
    },
  })
);

const AddNode = () => {
  const classes = useStyles();
  const [fromOpen, setFromOpen] = useState(false);

  const onAddPointClick = useCallback(() => {
    setFromOpen((prev) => !prev);
  }, []);

  const setFromClosed = useCallback(() => {
    setFromOpen(false);
  }, []);

  return (
    <div className={classes.root}>
      <div className={classes.button}>
        <AddButton onClick={onAddPointClick}>add Point</AddButton>
      </div>
      <Fade in={fromOpen} mountOnEnter unmountOnExit>
        <div>
          <AddNodeForm setFromClosed={setFromClosed} />
        </div>
      </Fade>
    </div>
  );
};

export default memo(AddNode);

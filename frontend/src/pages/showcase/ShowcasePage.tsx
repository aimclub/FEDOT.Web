import React, { FC, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import { getAllShowCases } from "../../redux/showCase/showCase-actions";
import { StateType } from "../../redux/store";
import ShowcaseCases from "./cases/ShowcaseCases";
import ShowcaseInfo from "./info/ShowcaseInfo";

const useStyles = makeStyles(() => ({
  root: {
    display: "grid",
    gridAutoColumns: "minmax(500px, 2fr) 1fr",
    gridAutoFlow: "column",
    gap: 20,
    alignItems: "flex-start",
  },
}));

const ShowCase: FC = () => {
  const classes = useStyles();
  const { showCase } = useSelector((state: StateType) => state.showCase);
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(getAllShowCases());
  }, [dispatch]);

  return (
    <div className={classes.root}>
      {showCase?.case_id ? (
        <>
          <ShowcaseInfo />
          <ShowcaseCases />
        </>
      ) : (
        <ShowcaseCases />
      )}
    </div>
  );
};

export default ShowCase;

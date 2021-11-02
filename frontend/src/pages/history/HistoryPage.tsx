import React, { FC, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Redirect } from "react-router";

import { makeStyles } from "@material-ui/core/styles";

import { getHistory } from "../../redux/history/history-actions";
import { StateType } from "../../redux/store";
import { AppRoutesEnum } from "../../routes";
import HistoryGeneration from "./generation/HistoryGeneration";
import HistoryGraph from "./graph/HistoryGraph";
import HistoryModal from "./modal/HistoryModal";

const useStyles = makeStyles(() => ({
  root: {
    marginBottom: 20,

    display: "grid",
    gap: 20,
    gridTemplateColumns: "1fr auto",
    alignItems: "flex-start",
  },
}));

const HistoryPage: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { showCase } = useSelector((state: StateType) => state.showCase);

  useEffect(() => {
    if (showCase) {
      dispatch(getHistory(showCase.case_id));
    }
  }, [dispatch, showCase]);

  return showCase ? (
    <div className={classes.root}>
      <HistoryGraph />
      <HistoryGeneration />
      <HistoryModal />
    </div>
  ) : (
    <Redirect to={AppRoutesEnum.SHOWCASE} />
  );
};

export default HistoryPage;

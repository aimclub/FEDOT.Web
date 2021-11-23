import React, { FC, useEffect } from "react";
import { useDispatch } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import { useAppParams } from "../../hooks/useAppParams";
import {
  getGenerationGeno,
  getGenerationPheno,
  getHistory,
} from "../../redux/history/history-actions";
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
  const { caseId } = useAppParams();
  const dispatch = useDispatch();

  useEffect(() => {
    if (caseId) {
      dispatch(getHistory(caseId));
      dispatch(getGenerationGeno(caseId));
      dispatch(getGenerationPheno(caseId));
    }
  }, [dispatch, caseId]);

  return (
    <div className={classes.root}>
      <HistoryGraph />
      <HistoryGeneration />
      <HistoryModal />
    </div>
  );
};

export default HistoryPage;

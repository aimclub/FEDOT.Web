import HistoryGeneration from "./generation/HistoryGeneration";
import HistoryGraph from "./graph/HistoryGraph";
import scss from "./historyPage.module.scss";
// import React, { FC, useEffect } from "react";
// import { useDispatch } from "react-redux";

// import { makeStyles } from "@material-ui/core/styles";

// import { useAppParams } from "../../hooks/useAppParams";
// import {
//   getGenerationGeno,
//   getGenerationPheno,
//   getHistory,
// } from "../../redux/history/history-actions";
// import HistoryGeneration from "./generation/HistoryGeneration";
// import HistoryGraph from "./graph/HistoryGraph";
// import HistoryModal from "./modal/HistoryModal";

const HistoryPage = () => {
  // const { caseId } = useAppParams();
  // const dispatch = useDispatch();

  // useEffect(() => {
  //   if (caseId) {
  //     dispatch(getHistory(caseId));
  //     dispatch(getGenerationGeno(caseId));
  //     dispatch(getGenerationPheno(caseId));
  //   }
  // }, [dispatch, caseId]);

  return (
    <div className={scss.root}>
      <HistoryGraph />
      <HistoryGeneration />
      {/* <HistoryModal /> */}
    </div>
  );
};

export default HistoryPage;

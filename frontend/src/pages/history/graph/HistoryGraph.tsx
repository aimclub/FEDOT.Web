import React, { FC, useEffect, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import styles from "./HistoryGraph.module.scss";

import { IHistoryNodeIndividual } from "../../../API/composer/composerInterface";
import AppLoader from "../../../components/UI/loaders/AppLoader";
import { openHistoryModal } from "../../../redux/history/history-actions";
import { StateType } from "../../../redux/store";
import { runHistory } from "../../../utils/historyGraphGenerator";

const useStyles = makeStyles(() => ({
  root: {
    padding: 8,
    height: "calc(100vh - 110px)",
    boxSizing: "border-box",

    background: "#FFFFFF",
    borderRadius: 8,
  },
  empty: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 24,
    lineHeight: "100%",
    textAlign: "center",

    color: "#cfd8dc",
  },
}));

const HistoryGraph: FC = () => {
  const classes = useStyles();
  const containerRef = useRef(null);
  const dispatch = useDispatch();
  const { history, isLoadingHistory } = useSelector(
    (state: StateType) => state.history
  );

  useEffect(() => {
    if (isLoadingHistory || !history || history.edges.length === 0) return;

    const nodeHoverTooltip = () => {};
    // const nodeHoverTooltip = useCallback((node) => {
    //   return `<div>
    //       <p >${node}</p>
    //     </div>`;
    // }, []);

    const handleNodeClick = (value: IHistoryNodeIndividual) => {
      dispatch(openHistoryModal(value));
    };

    if (containerRef.current) {
      const { destroy } = runHistory(
        containerRef.current,
        history.edges,
        history.nodes,
        nodeHoverTooltip,
        handleNodeClick
      );
      return destroy;
    }

    return undefined;
  }, [history, isLoadingHistory, dispatch]);

  return (
    <section className={classes.root}>
      <div ref={containerRef} className={styles.container}>
        {isLoadingHistory && <AppLoader />}
        {!history && !isLoadingHistory && (
          <p className={classes.empty}>no data</p>
        )}
      </div>
    </section>
  );
};

export default HistoryGraph;

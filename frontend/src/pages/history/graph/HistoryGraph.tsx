import React, { FC, useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { IconButton } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import FormatColorResetIcon from "@material-ui/icons/FormatColorReset";

import styles from "./HistoryGraph.module.scss";

import { IHistoryNodeIndividual } from "../../../API/composer/composerInterface";
import AppLoader from "../../../components/UI/loaders/AppLoader";
import CustomTooltip from "../../../components/UI/tooltip/CustomTooltip";
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
    position: "relative",
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
  resetSelect: {
    padding: 4,

    color: "#263238",

    position: "absolute",
    top: 15,
    left: 15,
    zIndex: 200,
  },
}));

const HistoryGraph: FC = () => {
  const classes = useStyles();
  const containerRef = useRef(null);
  const dispatch = useDispatch();
  const { history, isLoadingHistory } = useSelector(
    (state: StateType) => state.history
  );
  const [highlightPipelines, setHighlightPipelines] = useState<string[]>([]);
  const [zoom, setZoom] = useState<string | undefined>(undefined);

  const handleSelectReset = () => {
    setHighlightPipelines([]);
  };

  useEffect(() => {
    if (isLoadingHistory || !history || history.edges.length === 0) return;

    const handlePipelineClick = (value: IHistoryNodeIndividual) => {
      let arr: string[] = [value.uid];

      const fun = (pipelineUid: string) => {
        const t = history.edges
          .filter((i) => i.target === pipelineUid)
          .map((i) => i.source);
        arr.push(...t);
        t.forEach((i) => fun(i));
      };

      fun(value.uid);
      setHighlightPipelines(arr);
    };

    const handlePipelineDblClick = (value: IHistoryNodeIndividual) => {
      dispatch(openHistoryModal(value));
    };

    // const nodeHoverTooltip = useCallback((node) => {
    //   return `<div>
    //       <p >${node}</p>
    //     </div>`;
    // }, []);

    if (containerRef.current) {
      const { destroy } = runHistory(
        containerRef.current,
        history.edges,
        history.nodes,
        highlightPipelines,
        handlePipelineClick,
        handlePipelineDblClick,
        { zoom, setZoom }
      );
      return destroy;
    }

    return undefined;

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [history, isLoadingHistory, dispatch, highlightPipelines]);

  return (
    <section className={classes.root}>
      {!!history && !isLoadingHistory && (
        <CustomTooltip title="reset select" placement="top-start">
          <span>
            <IconButton
              className={classes.resetSelect}
              disabled={highlightPipelines.length === 0}
              onClick={handleSelectReset}
            >
              <FormatColorResetIcon />
            </IconButton>
          </span>
        </CustomTooltip>
      )}

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

import scss from "./HistoryGraph.module.scss";

import { useCallback, useEffect, useRef, useState } from "react";

import FormatColorResetIcon from "@mui/icons-material/FormatColorReset";
import IconButton from "@mui/material/IconButton";

import { composerAPI } from "../../../API/composer/composerAPI";
import { IHistoryNodeIndividual } from "../../../API/composer/composerInterface";
import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import CustomTooltip from "../../../components/UI/tooltip/CustomTooltip";
import { useAppParams } from "../../../hooks/useAppParams";
import { cl } from "../../../utils/classnames";
import {
  ZoomType,
  createHistoryGraph,
} from "../../../utils/historyGraphGenerator";
import HistoryModal from "../modal/HistoryModal";

const HistoryGraph = () => {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const { caseId } = useAppParams();
  const { isFetching, data, isError } = composerAPI.useGetHistoryGraphQuery(
    { caseId: caseId || "" },
    { skip: !caseId }
  );
  const [highlightPipelines, setHighlightPipelines] = useState<string[]>([]);
  const [nodeModal, setNodeModal] = useState<IHistoryNodeIndividual | null>(
    null
  );
  const zoom = useRef<ZoomType>();

  const handleSelectReset = useCallback(() => {
    setHighlightPipelines([]);
  }, []);

  const handleModalClose = useCallback(() => {
    setNodeModal(null);
  }, []);

  useEffect(() => {
    if (!graphRef.current || isFetching || !data) return;

    const handlePipelineClick = (value: IHistoryNodeIndividual) => {
      const arr: string[] = [value.uid];
      const fun = (pipelineUid: string) => {
        const t = data.edges
          .filter((i) => i.target === pipelineUid)
          .map((i) => i.source);
        arr.push(...t);
        t.forEach((i) => fun(i));
      };
      fun(value.uid);
      setHighlightPipelines(arr);
    };

    const { destroy } = createHistoryGraph(
      graphRef.current,
      data.edges,
      data.nodes,
      highlightPipelines,
      handlePipelineClick,
      (node) => {
        setNodeModal(node);
      },
      { zoom: zoom.current, setZoom: (v) => (zoom.current = v) }
    );
    return destroy;
  }, [data, highlightPipelines, isFetching]);

  return (
    <section className={scss.root}>
      <div ref={graphRef} className={scss.graph} />

      {isFetching ? (
        <AppLoader className={scss.center} />
      ) : !data || isError ? (
        <p className={cl(scss.empty, scss.center)}>no data</p>
      ) : (
        <CustomTooltip title="reset select" placement="top-start">
          <span className={scss.tools}>
            <IconButton
              onClick={handleSelectReset}
              className={scss.button}
              disabled={highlightPipelines.length === 0}
            >
              <FormatColorResetIcon />
            </IconButton>
          </span>
        </CustomTooltip>
      )}

      <HistoryModal node={nodeModal} onClose={handleModalClose} />
    </section>
  );
};

export default HistoryGraph;

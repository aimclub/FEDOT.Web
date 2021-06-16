import React, { FC, useEffect, useState } from "react";
import HistoryGraph from "../../components/HistoryGraph/HistoryGraph";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../store/store";
import { getHistoryGraph } from "../../store/sandbox-reducer";
import HistoryModal from "../../components/HistoryGraph/HistoryModal/HistoryModal";

interface IHistory {}

const History: FC<IHistory> = (props) => {
  const [open, setOpen] = useState(false);
  const dispatch = useDispatch();
  const nodeHoverTooltip = React.useCallback((node) => {
    return `<div>     
      <p >${node}</p>
    </div>`;
  }, []);

  useEffect(() => {
    dispatch(getHistoryGraph(45454));
  }, [dispatch]);

  const { historyGraph } = useSelector(
    (state: StateType) => state.sandboxReducer
  );

  return (
    <>
      <HistoryGraph
        edgesData={historyGraph.edges}
        nodesData={historyGraph.nodes}
        onClick={(v) => {
          setOpen(true);
        }}
        nodeHoverTooltip={nodeHoverTooltip}
      />
      <HistoryModal open={open} handleClose={() => setOpen(false)} />
    </>
  );
};
export default History;

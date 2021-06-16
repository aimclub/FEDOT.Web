import React, { FC, useEffect } from "react";
import HistoryGraph from "../../components/HistoryGraph/HistoryGraph";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../store/store";
import { getHistoryGraph } from "../../store/sandbox-reducer";

interface IHistory {}

const History: FC<IHistory> = (props) => {
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
    <HistoryGraph
      edgesData={historyGraph.edges}
      nodesData={historyGraph.nodes}
      onClick={(v) => {
        console.log(v);
      }}
      nodeHoverTooltip={nodeHoverTooltip}
    />
  );
};
export default History;

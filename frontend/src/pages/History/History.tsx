import React, { FC, useEffect, useState } from "react";
import HistoryGraph from "../../components/HistoryGraph/HistoryGraph";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../store/store";
import { getHistoryGraph } from "../../store/sandbox-reducer";
import HistoryModal from "../../components/HistoryGraph/HistoryModal/HistoryModal";
import { useLocation } from "react-router-dom";
import { deserializeQuery } from "../../utils/query-helpers";

interface IHistory {}

const History: FC<IHistory> = (props) => {
  const [uidModal, setUidModal] = useState("");
  const { search } = useLocation();
  const dispatch = useDispatch();
  const nodeHoverTooltip = React.useCallback((node) => {
    return `<div>     
      <p >${node}</p>
    </div>`;
  }, []);

  useEffect(() => {
    if (search) {
      const { uid } = deserializeQuery(search);
      dispatch(getHistoryGraph(uid));
    }
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
          setUidModal(v);
        }}
        nodeHoverTooltip={nodeHoverTooltip}
      />
      {uidModal && (
        <HistoryModal
          uid={uidModal}
          handleClose={() => {
            setUidModal("");
          }}
        />
      )}
    </>
  );
};
export default History;

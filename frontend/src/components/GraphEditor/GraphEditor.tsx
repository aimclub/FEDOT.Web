import React, { FC, useEffect } from "react";
import { Paper } from "@material-ui/core";
import GraphEditorDirectedGraph from "./GraphEditorDirectedGraph/GraphEditorDirectedGraph";
import { actionsSandbox, getMainGraph } from "../../store/sandbox-reducer";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../store/store";
import GraphEditorModal from "./GraphEditorModal/GraphEditorModal";
import { makeStyles } from "@material-ui/core/styles";
import { useLocation } from "react-router-dom";
import { deserializeQuery } from "../../utils/query-helpers";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    display: "flex",
  },
}));

interface IGraphEditor {}

const GraphEditor: FC<IGraphEditor> = (props) => {
  const classes = useStyles();
  const { search } = useLocation();
  const dispatch = useDispatch();

  const { mainGraph } = useSelector((state: StateType) => state.sandboxReducer);

  useEffect(() => {
    if (search) {
      const { uid } = deserializeQuery(search);
      dispatch(getMainGraph(uid));
    }
  }, [dispatch, search]);

  useEffect(() => {
    console.log(`### mainGraph`, mainGraph);
  }, [mainGraph]);

  return (
    <Paper elevation={3} className={classes.root}>
      {mainGraph && (
        <GraphEditorDirectedGraph
          edgesData={mainGraph.edges}
          nodesData={mainGraph.nodes}
        />
      )}
    </Paper>
  );
};
export default GraphEditor;

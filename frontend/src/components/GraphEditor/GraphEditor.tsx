import React, { FC, useEffect } from "react";
import { Paper } from "@material-ui/core";
import GraphEditorDirectedGraph from "./GraphEditorDirectedGraph/GraphEditorDirectedGraph";
import { actionsSandbox, getMainGraph } from "../../store/sandbox-reducer";
import { useDispatch, useSelector } from "react-redux";
import { StateType } from "../../store/store";
import GraphEditorModal from "./GraphEditorModal/GraphEditorModal";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    display: "flex",
  },
}));

interface IGraphEditor {}

const GraphEditor: FC<IGraphEditor> = (props) => {
  const classes = useStyles();
  const dispatch = useDispatch();

  const { mainGraph } = useSelector((state: StateType) => state.sandboxReducer);

  useEffect(() => {
    dispatch(getMainGraph(45454));
  }, [dispatch]);

  const handleAddNode = (d: any): any => {
    const newNode = { ...mainGraph.nodes[0], id: mainGraph.nodes.length };
    const newEdge = { source: newNode.id, target: d };
    console.log(`### newNode`, newNode);
    dispatch(
      actionsSandbox.addNodeMainGraph({
        nodes: [newNode],
        edges: [newEdge],
      })
    );
    console.log(`### handleAddNode d`, d);
  };

  const handleDeleteNode = (d: any): any => {
    dispatch(actionsSandbox.toggleEditModal());
    // dispatch(actionsSandbox.deleteNodeMainGraph(d));
    console.log(`### handleDeleteNode d`, d);
  };
  return (
    <Paper elevation={3} className={classes.root}>
      {mainGraph && (
        <GraphEditorDirectedGraph
          edgesData={mainGraph.edges}
          nodesData={mainGraph.nodes}
          onClickAddNode={handleAddNode}
          onClickDeleteNode={handleDeleteNode}
        />
      )}
      <GraphEditorModal />
    </Paper>
  );
};
export default GraphEditor;

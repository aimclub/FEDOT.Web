import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { INodeData, IPipeline } from "../../API/pipeline/pipelineInterface";
import { IPipelineNodesEdgesValues } from "../../components/forms/pipelineNode/edges/PipelineNodeEdgesForm";

export type PipelineNodeEdgesType = "add" | "edit" | null;

export const initialState = {
  pipeline_uid: "",
  pipeline: undefined as IPipeline | undefined,
  pipeline_menu_node_id: null as number | null,
  pipeline_node_params: {
    open: false,
    node: null as INodeData | null,
  },
  pipeline_node_edges: {
    type: null as PipelineNodeEdgesType,
    node: null as INodeData | null,
  },
};

export const sandboxSlice = createSlice({
  name: "sandbox",
  initialState,
  reducers: {
    setPipelineUid: (state, { payload }: PayloadAction<string>) => {
      state.pipeline_uid = payload;
    },

    setPipeline: (state, { payload }: PayloadAction<IPipeline | undefined>) => {
      state.pipeline = payload;
      state.pipeline_menu_node_id = null;
      state.pipeline_node_edges.type = null;
      state.pipeline_node_params.open = false;
    },

    setPipelineMenuNode: (state, { payload }: PayloadAction<number | null>) => {
      state.pipeline_menu_node_id = payload;
    },

    setPipelineNodeEdgesType: (
      state,
      { payload }: PayloadAction<PipelineNodeEdgesType>
    ) => {
      state.pipeline_node_edges.type = payload;
      state.pipeline_node_edges.node =
        payload === "edit"
          ? state.pipeline?.nodes.find(
              (n) => n.id === state.pipeline_menu_node_id
            ) || null
          : null;
      state.pipeline_node_params.open = false;
    },

    setPipelineNodeParamsOpen: (state, { payload }: PayloadAction<boolean>) => {
      state.pipeline_node_params.open = payload;
      state.pipeline_node_params.node = payload
        ? state.pipeline?.nodes.find(
            (n) => n.id === state.pipeline_menu_node_id
          ) || null
        : null;
      state.pipeline_node_edges.type = null;
    },

    editPipelineNodeEdges: (
      state,
      { payload }: PayloadAction<IPipelineNodesEdgesValues>
    ) => {
      if (!state.pipeline) return;

      const currentNode = state.pipeline_node_edges.node;
      const nodeId =
        currentNode?.id !== undefined
          ? currentNode.id
          : Math.max(...state.pipeline.nodes.map((i) => i.id), 0) + 1;

      if (currentNode) {
        // обновляем данные node
        const index = state.pipeline.nodes.findIndex(
          (n) => n.id === currentNode.id
        );
        state.pipeline.nodes[index] = {
          ...state.pipeline.nodes[index],
          display_name: payload.display_name,
          type: payload.type || "model",
          parents: payload.parents,
          children: payload.children,
        };
        // удаляем данные о старых связях
        state.pipeline.nodes = state.pipeline.nodes.map((node) => ({
          ...node,
          children: node.children.filter((c) => c !== currentNode.id),
          parents: node.parents.filter((p) => p !== currentNode.id),
        }));
        state.pipeline.edges = state.pipeline.edges.filter(
          ({ source, target }) =>
            source !== currentNode.id && target !== currentNode.id
        );
      } else {
        // добавляем данные node
        state.pipeline.nodes = state.pipeline.nodes.concat([
          {
            id: nodeId,
            display_name: payload.display_name,
            model_name: payload.display_name,
            type: payload.type || "model",
            params: {},
            parents: payload.parents,
            children: payload.children,
          },
        ]);
      }
      // добавляем новые связи
      payload.parents?.forEach((parentId) => {
        if (!state.pipeline) return;
        const index = state.pipeline.nodes.findIndex((n) => n.id === parentId);
        state.pipeline.nodes[index].children =
          state.pipeline.nodes[index].children.concat(nodeId);
      });

      payload.children?.forEach((childrenId) => {
        if (!state.pipeline) return;
        const index = state.pipeline.nodes.findIndex(
          (n) => n.id === childrenId
        );
        state.pipeline.nodes[index].parents =
          state.pipeline.nodes[index].parents.concat(nodeId);
      });

      state.pipeline.edges = state.pipeline.edges.concat(
        payload.children.map((target) => ({ target, source: nodeId })),
        payload.parents.map((source) => ({ target: nodeId, source }))
      );
    },

    editPipelineNodeParams: (state, { payload }: PayloadAction<INodeData>) => {
      if (!state.pipeline) return;
      const nodeIndex = state.pipeline?.nodes.findIndex(
        (n) => n.id === payload.id
      );
      state.pipeline.nodes[nodeIndex] = payload;
    },

    deletePipelineNode: (state) => {
      state.pipeline_node_edges.type = null;
      state.pipeline_node_params.open = false;

      const deleteNodeId = state.pipeline_menu_node_id;
      state.pipeline_menu_node_id = null;
      if (state.pipeline) {
        state.pipeline.edges = state.pipeline.edges.filter(
          ({ source, target }) =>
            source !== deleteNodeId && target !== deleteNodeId
        );

        state.pipeline.nodes = state.pipeline.nodes
          .filter((node) => node.id !== deleteNodeId)
          .map((node) => ({
            ...node,
            children: node.children.filter((c) => c !== deleteNodeId),
            parents: node.parents.filter((p) => p !== deleteNodeId),
          }));
      }
    },
  },
});

export const {
  setPipelineUid,
  setPipeline,
  setPipelineMenuNode,
  setPipelineNodeParamsOpen,
  setPipelineNodeEdgesType,
  editPipelineNodeEdges,
  editPipelineNodeParams,
  deletePipelineNode,
} = sandboxSlice.actions;
export const { reducer: sandboxReducer, name: sandboxReducerName } =
  sandboxSlice;

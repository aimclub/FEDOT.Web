import { pipelineAPI } from "../../API/pipeline/pipelineAPI";
import {
  IEdgeData,
  INodeData,
  IPipeline,
} from "../../API/pipeline/pipelineInterface";
import { getResult } from "../sandbox/sandbox-actions";
import {
  AddPipelineNode,
  ClosePointEdit,
  DeletePipelineNode,
  MenuPositionType,
  OpenPointEdit,
  PipelineActionsEnum,
  ResetPipeline,
  SandboxPointFormType,
  SetMenuClose,
  SetMenuOpen,
  SetNodeEditData,
  SetNodeEditOpen,
  SetPipeline,
  SetPipelineEvaluating,
  SetPipelineFromHistory,
  SetPipelineLoading,
  ThunkType,
  ThunkTypeAsync,
} from "./pipeline-types";

export const actionsPipeline = {
  addPipelineNode: (data: {
    node: INodeData;
    edges: IEdgeData[];
  }): AddPipelineNode => ({
    type: PipelineActionsEnum.PIPELINE_NODE_ADD,
    data,
  }),
  deletePipelineNode: (nodeId: number): DeletePipelineNode => ({
    type: PipelineActionsEnum.PIPELINE_NODE_DELETE,
    data: nodeId,
  }),
  editPipelineNode:
    (pipeline: IPipeline, node: INodeData, edges: IEdgeData[]): ThunkType =>
    (dispatch) => {
      const nodesEdit = pipeline.nodes.filter((item) => item.id !== node.id);
      const edgesEdit = pipeline.edges.filter(
        (item) => item.source !== node.id && item.target !== node.id
      );

      dispatch(
        actionsPipeline.setPipeline({
          ...pipeline,
          nodes: nodesEdit,
          edges: edgesEdit,
        })
      );
      dispatch(actionsPipeline.addPipelineNode({ node, edges }));
    },
  closeAllModals: (): ThunkType => (dispatch) => {
    dispatch(actionsPipeline.closePointEdit());
    dispatch(actionsPipeline.setNodeEditOpen(false));
    dispatch(actionsPipeline.setMenuClose());
  },
  closePointEdit: (): ClosePointEdit => ({
    type: PipelineActionsEnum.POINT_EDIT_CLOSE,
  }),
  openPointEdit: (data: {
    type: SandboxPointFormType;
    node?: INodeData;
  }): OpenPointEdit => ({
    type: PipelineActionsEnum.POINT_EDIT_OPEN,
    data,
  }),
  setMenuClose: (): SetMenuClose => ({ type: PipelineActionsEnum.MENU_CLOSE }),
  setMenuOpen: (data: {
    nodeId: number;
    position: MenuPositionType;
  }): SetMenuOpen => ({ type: PipelineActionsEnum.MENU_OPEN, data }),
  setNodeEditData: (data: INodeData): SetNodeEditData => ({
    type: PipelineActionsEnum.NODE_EDIT_DATA,
    data,
  }),
  setNodeEditOpen: (data: boolean): SetNodeEditOpen => ({
    type: PipelineActionsEnum.NODE_EDIT_OPEN,
    data,
  }),
  setPipeline: (pipeline: IPipeline, isFromHistory?: boolean): SetPipeline => ({
    type: PipelineActionsEnum.PIPELINE,
    data: { pipeline, isFromHistory: isFromHistory || false },
  }),
  setPipelineFromHistory: (data: boolean): SetPipelineFromHistory => ({
    type: PipelineActionsEnum.PIPELINE_FROM_HISTORY,
    data,
  }),
  setPipelineEvaluating: (data: boolean): SetPipelineEvaluating => ({
    type: PipelineActionsEnum.PIPELINE_EVALUATING,
    data,
  }),
  setPipelineLoading: (data: boolean): SetPipelineLoading => ({
    type: PipelineActionsEnum.PIPELINE_LOADING,
    data,
  }),
  resetPipeline: (): ResetPipeline => ({
    type: PipelineActionsEnum.RESET_PIPELINE,
  }),
};

export const getPipeline =
  (uid: string, isFromHistory?: boolean): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsPipeline.closeAllModals());
    dispatch(actionsPipeline.setPipelineLoading(true));
    try {
      const data = await pipelineAPI.getPipeline(uid);
      dispatch(actionsPipeline.setPipeline(data, isFromHistory));
      dispatch(actionsPipeline.setPipelineLoading(false));
    } catch (error) {
      console.log(error);
    }
  };

export const evaluatePipeline =
  (uid: string, nodes: INodeData[], edges: IEdgeData[]): ThunkTypeAsync =>
  async (dispatch, getState) => {
    dispatch(actionsPipeline.setPipelineEvaluating(true));
    try {
      const res = await pipelineAPI.validatePipeline({ uid, nodes, edges });
      if (res.is_valid) {
        const data = await pipelineAPI.postPipeline({ uid, nodes, edges });
        if (data.is_new) {
          alert("Graph is valid. Added.");
          dispatch(getPipeline(data.uid));
          dispatch(getResult(getState().showCase.showCase?.case_id!, data.uid));
        }
      } else {
        alert(res.error_desc);
      }
    } catch (error) {
      alert(error);
      console.log(error);
    } finally {
      dispatch(actionsPipeline.setPipelineEvaluating(false));
    }
  };

export const resetPipeline = (): ThunkType => (dispatch) => {
  dispatch(actionsPipeline.resetPipeline());
};

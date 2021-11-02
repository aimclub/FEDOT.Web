import { metaAPI } from "../../API/meta/metaAPI";
import { IModelName } from "../../API/meta/metaInterface";
import { pipelineAPI } from "../../API/pipeline/pipelineAPI";
import {
  IEdgeData,
  INodeData,
  IPipeline,
} from "../../API/pipeline/pipelineInterface";
import { setPipelineUid } from "../sandbox/sandbox-actions";
import {
  AddPipelineNode,
  ClosePointEdit,
  DeletePipelineNode,
  MenuPositionType,
  OpenPointEdit,
  PipelineActionsEnum,
  SandboxPointFormType,
  SetMenuClose,
  SetMenuOpen,
  SetModelNames,
  SetNodeEditData,
  SetNodeEditOpen,
  SetPipeline,
  SetPipelineEvaluating,
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
  getModelNames:
    (taskId: string): ThunkTypeAsync =>
    async (dispatch) => {
      try {
        const modelNames = await metaAPI.getAllModelName(taskId);
        dispatch(actionsPipeline.setModelNames(modelNames));
      } catch (error) {
        console.log(error);
        return Promise.reject(error);
      }
    },
  getPipeline:
    (uid: string): ThunkTypeAsync =>
    async (dispatch) => {
      dispatch(actionsPipeline.closeAllModals());
      dispatch(actionsPipeline.setPipelineLoading(true));
      try {
        const data = await pipelineAPI.getPipeline(uid);
        dispatch(actionsPipeline.setPipeline(data));
        dispatch(actionsPipeline.setPipelineLoading(false));
      } catch (error) {
        console.log(error);
      }
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
  setModelNames: (data: IModelName[]): SetModelNames => ({
    type: PipelineActionsEnum.MODEL_NAMES,
    data,
  }),
  setNodeEditData: (data: INodeData): SetNodeEditData => ({
    type: PipelineActionsEnum.NODE_EDIT_DATA,
    data,
  }),
  setNodeEditOpen: (data: boolean): SetNodeEditOpen => ({
    type: PipelineActionsEnum.NODE_EDIT_OPEN,
    data,
  }),
  setPipeline: (data: IPipeline): SetPipeline => ({
    type: PipelineActionsEnum.PIPELINE,
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
};

export const evaluatePipeline =
  (uid: string, nodes: INodeData[], edges: IEdgeData[]): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsPipeline.setPipelineEvaluating(true));
    try {
      const res = await pipelineAPI.validatePipeline({ uid, nodes, edges });
      if (res.is_valid) {
        const data = await pipelineAPI.postPipeline({ uid, nodes, edges });
        if (data.is_new) {
          dispatch(setPipelineUid(data.uid, "evaluate"));
          alert("Graph is valid. Added.");
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

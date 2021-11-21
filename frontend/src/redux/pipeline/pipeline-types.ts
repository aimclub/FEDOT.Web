import { ThunkAction } from "redux-thunk";
import {
  IEdgeData,
  INodeData,
  IPipeline,
} from "../../API/pipeline/pipelineInterface";
import { StateType } from "../store";
import { initialState } from "./pipeline-reducer";

export enum PipelineActionsEnum {
  MENU_CLOSE = "MENU_CLOSE",
  MENU_OPEN = "MENU_OPEN",
  NODE_EDIT_DATA = "NODE_EDIT_DATA",
  NODE_EDIT_OPEN = "NODE_EDIT_OPEN",
  PIPELINE = "PIPELINE",
  PIPELINE_FROM_HISTORY = "PIPELINE_FROM_HISTORY",
  PIPELINE_EVALUATING = "PIPELINE_EVALUATING",
  PIPELINE_LOADING = "PIPELINE_LOADING",
  PIPELINE_NODE_ADD = "PIPELINE_NODE_ADD",
  PIPELINE_NODE_DELETE = "PIPELINE_NODE_DELETE",
  POINT_EDIT_CLOSE = "POINT_EDIT_CLOSE",
  POINT_EDIT_OPEN = "POINT_EDIT_OPEN",
  RESET_PIPELINE = "RESET_PIPELINE",
}

export enum SandboxPointFormType {
  ADD_NEW = "ADD_NEW",
  EDIT = "EDIT",
}

export type MenuPositionType = {
  x: number;
  y: number;
};

export type InitialStateType = typeof initialState;

export type ThunkTypeAsync = ThunkAction<
  Promise<void>,
  StateType,
  unknown,
  AllTypes
>;

export type ThunkType = ThunkAction<void, StateType, unknown, AllTypes>;

export type AllTypes =
  | AddPipelineNode
  | ClosePointEdit
  | DeletePipelineNode
  | OpenPointEdit
  | SetMenuClose
  | SetMenuOpen
  | SetNodeEditData
  | SetNodeEditOpen
  | SetPipeline
  | SetPipelineFromHistory
  | SetPipelineLoading
  | SetPipelineEvaluating
  | ResetPipeline;

export type AddPipelineNode = {
  type: PipelineActionsEnum.PIPELINE_NODE_ADD;
  data: { node: INodeData; edges: IEdgeData[] };
};

export type ClosePointEdit = {
  type: PipelineActionsEnum.POINT_EDIT_CLOSE;
};

export type DeletePipelineNode = {
  type: PipelineActionsEnum.PIPELINE_NODE_DELETE;
  data: number;
};

export type OpenPointEdit = {
  type: PipelineActionsEnum.POINT_EDIT_OPEN;
  data: {
    type: SandboxPointFormType;
    node?: INodeData;
  };
};

export type SetMenuClose = {
  type: PipelineActionsEnum.MENU_CLOSE;
};

export type SetMenuOpen = {
  type: PipelineActionsEnum.MENU_OPEN;
  data: { nodeId: number; position: MenuPositionType };
};

export type SetNodeEditData = {
  type: PipelineActionsEnum.NODE_EDIT_DATA;
  data: INodeData;
};

export type SetNodeEditOpen = {
  type: PipelineActionsEnum.NODE_EDIT_OPEN;
  data: boolean;
};

export type SetPipeline = {
  type: PipelineActionsEnum.PIPELINE;
  data: { pipeline: IPipeline; isFromHistory: boolean };
};

export type SetPipelineFromHistory = {
  type: PipelineActionsEnum.PIPELINE_FROM_HISTORY;
  data: boolean;
};

export type SetPipelineLoading = {
  type: PipelineActionsEnum.PIPELINE_LOADING;
  data: boolean;
};

export type SetPipelineEvaluating = {
  type: PipelineActionsEnum.PIPELINE_EVALUATING;
  data: boolean;
};

export type ResetPipeline = {
  type: PipelineActionsEnum.RESET_PIPELINE;
};

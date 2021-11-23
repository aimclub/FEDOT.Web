import { INodeData, IPipeline } from "../../API/pipeline/pipelineInterface";
import {
  AllTypes,
  InitialStateType,
  MenuPositionType,
  PipelineActionsEnum,
  SandboxPointFormType,
} from "./pipeline-types";

export const initialState = {
  isFromHistory: false,
  isEvaluatingPipeline: false,
  isLoadingPipeline: false,
  menu: {
    isOpen: false,
    nodeId: undefined as number | undefined,
    position: {} as MenuPositionType,
  },
  pointEdit: {
    isOpen: false,
    type: SandboxPointFormType.ADD_NEW,
    node: {} as INodeData,
  },
  nodeEdit: {
    isOpen: false,
    node: {} as INodeData,
  },
  pipeline: { nodes: [], edges: [], uid: "" } as IPipeline,
};

const pipelineReducer = (
  state = initialState,
  action: AllTypes
): InitialStateType => {
  switch (action.type) {
    case PipelineActionsEnum.MENU_CLOSE:
      return {
        ...state,
        menu: {
          isOpen: false,
          nodeId: undefined,
          position: {} as MenuPositionType,
        },
      };

    case PipelineActionsEnum.MENU_OPEN:
      return {
        ...state,
        menu: {
          isOpen: true,
          nodeId: action.data.nodeId,
          position: action.data.position,
        },
      };

    case PipelineActionsEnum.NODE_EDIT_DATA:
      return {
        ...state,
        nodeEdit: { ...state.nodeEdit, node: action.data },
      };

    case PipelineActionsEnum.NODE_EDIT_OPEN:
      return {
        ...state,
        nodeEdit: { ...state.nodeEdit, isOpen: action.data },
      };

    case PipelineActionsEnum.PIPELINE:
      return {
        ...state,
        isFromHistory: action.data.isFromHistory,
        pipeline: action.data.pipeline,
      };

    case PipelineActionsEnum.PIPELINE_FROM_HISTORY:
      return {
        ...state,
        isFromHistory: action.data,
      };

    case PipelineActionsEnum.PIPELINE_LOADING:
      return { ...state, isLoadingPipeline: action.data };

    case PipelineActionsEnum.PIPELINE_EVALUATING:
      return { ...state, isEvaluatingPipeline: action.data };

    case PipelineActionsEnum.PIPELINE_NODE_ADD:
      return {
        ...state,
        pipeline: {
          ...state.pipeline,
          nodes: state.pipeline.nodes.concat(action.data.node),
          edges: state.pipeline.edges.concat(action.data.edges),
        },
      };

    case PipelineActionsEnum.PIPELINE_NODE_DELETE:
      return {
        ...state,
        pipeline: {
          ...state.pipeline,
          nodes: state.pipeline.nodes
            .filter((item) => item.id !== +action.data)
            .map((item) => ({
              ...item,
              children: item.children.filter((c) => c !== +action.data),
              parents: item.parents.filter((p) => p !== +action.data),
            })),
          edges: state.pipeline.edges.filter(
            (item) =>
              item.source !== +action.data && item.target !== +action.data
          ),
        },
      };

    case PipelineActionsEnum.POINT_EDIT_CLOSE:
      return {
        ...state,
        pointEdit: {
          ...state.pointEdit,
          isOpen: false,
        },
      };

    case PipelineActionsEnum.POINT_EDIT_OPEN:
      return {
        ...state,
        pointEdit: {
          isOpen: true,
          type: action.data.type,
          node: action.data.node as INodeData,
        },
      };

    case PipelineActionsEnum.RESET_PIPELINE:
      return initialState;

    default:
      return state;
  }
};

export default pipelineReducer;

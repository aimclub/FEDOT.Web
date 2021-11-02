import {
  GenerationType,
  IGeneration,
} from "../../API/analytics/analyticsInterface";
import {
  IHistoryGraph,
  IHistoryNodeIndividual,
} from "../../API/composer/composerInterface";
import { IPipelineImage } from "../../API/pipeline/pipelineInterface";
import {
  AllTypes,
  HistoryActionsEnum,
  InitialStateType,
} from "./history-types";

export const initialState = {
  generationGeno: null as IGeneration | null,
  generationPheno: null as IGeneration | null,
  generationType: "pheno" as GenerationType,
  history: null as IHistoryGraph | null,
  isLoadingHistory: false,
  isLoadingGenerationGeno: false,
  isLoadingGenerationPheno: false,
  modal: {
    isLoadingPipelineImage: false,
    isOpen: false,
    pipeline: null as IHistoryNodeIndividual | null,
    pipelineImage: null as IPipelineImage | null,
  },
};

const historyReducer = (
  state = initialState,
  action: AllTypes
): InitialStateType => {
  switch (action.type) {
    case HistoryActionsEnum.GENERATION_GENO:
      return { ...state, generationGeno: action.data };

    case HistoryActionsEnum.GENERATION_GENO_LOADING:
      return { ...state, isLoadingGenerationGeno: action.data };

    case HistoryActionsEnum.GENERATION_PHENO:
      return { ...state, generationPheno: action.data };

    case HistoryActionsEnum.GENERATION_PHENO_LOADING:
      return { ...state, isLoadingGenerationPheno: action.data };

    case HistoryActionsEnum.GENERATION_TYPE:
      return { ...state, generationType: action.data };

    case HistoryActionsEnum.HISTORY:
      return { ...state, history: action.data };

    case HistoryActionsEnum.HISTORY_LOADING:
      return { ...state, isLoadingHistory: action.data };

    case HistoryActionsEnum.MODAL_OPEN:
      return { ...state, modal: { ...state.modal, isOpen: action.data } };

    case HistoryActionsEnum.MODAL_PIPELINE:
      return { ...state, modal: { ...state.modal, pipeline: action.data } };

    case HistoryActionsEnum.MODAL_PIPELINE_IMAGE:
      return {
        ...state,
        modal: { ...state.modal, pipelineImage: action.data },
      };

    case HistoryActionsEnum.MODAL_PIPELINE_IMAGE_LOADING:
      return {
        ...state,
        modal: { ...state.modal, isLoadingPipelineImage: action.data },
      };

    default:
      return state;
  }
};

export default historyReducer;

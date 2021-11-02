import { ThunkAction } from "redux-thunk";
import {
  GenerationType,
  IGeneration,
} from "../../API/analytics/analyticsInterface";
import {
  IHistoryGraph,
  IHistoryNodeIndividual,
} from "../../API/composer/composerInterface";
import { IPipelineImage } from "../../API/pipeline/pipelineInterface";
import { StateType } from "../store";
import { initialState } from "./history-reducer";

export enum HistoryActionsEnum {
  GENERATION_GENO = "GENERATION_GENO",
  GENERATION_GENO_LOADING = "GENERATION_GENO_LOADING",
  GENERATION_PHENO = "GENERATION_PHENO",
  GENERATION_PHENO_LOADING = "GENERATION_PHENO_LOADING",
  GENERATION_TYPE = "GENERATION_TYPE",
  HISTORY = "HISTORY",
  HISTORY_LOADING = "HISTORY_LOADING",
  MODAL_OPEN = "MODAL_OPEN",
  MODAL_PIPELINE = "MODAL_PIPELINE",
  MODAL_PIPELINE_IMAGE = "MODAL_PIPELINE_IMAGE",
  MODAL_PIPELINE_IMAGE_LOADING = "MODAL_PIPELINE_IMAGE_LOADING",
}

export type InitialStateType = typeof initialState;

export type AllTypes =
  | SetGenerationGeno
  | SetGenerationGenoLoading
  | SetGenerationPheno
  | SetGenerationPhenoLoading
  | SetGenerationType
  | SetHistory
  | SetHistoryLoading
  | SetModalOpen
  | SetModalPipeline
  | SetModalPipelineImage
  | SetModalPipelineImageLoading;

export type ThunkType = ThunkAction<void, StateType, unknown, AllTypes>;

export type ThunkTypeAsync = ThunkAction<
  Promise<void>,
  StateType,
  unknown,
  AllTypes
>;

export type SetGenerationGeno = {
  type: HistoryActionsEnum.GENERATION_GENO;
  data: IGeneration | null;
};

export type SetGenerationGenoLoading = {
  type: HistoryActionsEnum.GENERATION_GENO_LOADING;
  data: boolean;
};

export type SetGenerationPheno = {
  type: HistoryActionsEnum.GENERATION_PHENO;
  data: IGeneration | null;
};

export type SetGenerationPhenoLoading = {
  type: HistoryActionsEnum.GENERATION_PHENO_LOADING;
  data: boolean;
};

export type SetGenerationType = {
  type: HistoryActionsEnum.GENERATION_TYPE;
  data: GenerationType;
};

export type SetHistory = {
  type: HistoryActionsEnum.HISTORY;
  data: IHistoryGraph | null;
};

export type SetHistoryLoading = {
  type: HistoryActionsEnum.HISTORY_LOADING;
  data: boolean;
};

export type SetModalOpen = {
  type: HistoryActionsEnum.MODAL_OPEN;
  data: boolean;
};

export type SetModalPipeline = {
  type: HistoryActionsEnum.MODAL_PIPELINE;
  data: IHistoryNodeIndividual | null;
};

export type SetModalPipelineImage = {
  type: HistoryActionsEnum.MODAL_PIPELINE_IMAGE;
  data: IPipelineImage | null;
};

export type SetModalPipelineImageLoading = {
  type: HistoryActionsEnum.MODAL_PIPELINE_IMAGE_LOADING;
  data: boolean;
};

import {analyticsAPI} from "../../API/analytics/analyticsAPI";
import {GenerationType, IGeneration,} from "../../API/analytics/analyticsInterface";
import {composerAPI} from "../../API/composer/composerAPI";
import {IHistoryGraph, IHistoryNodeIndividual,} from "../../API/composer/composerInterface";
import {pipelineAPI} from "../../API/pipeline/pipelineAPI";
import {IPipelineImage} from "../../API/pipeline/pipelineInterface";
import {
    HistoryActionsEnum,
    SetGenerationGeno,
    SetGenerationGenoLoading,
    SetGenerationPheno,
    SetGenerationPhenoLoading,
    SetGenerationType,
    SetHistory,
    SetHistoryLoading,
    SetModalOpen,
    SetModalPipeline,
    SetModalPipelineImage,
    SetModalPipelineImageLoading,
    ThunkType,
    ThunkTypeAsync,
} from "./history-types";

const actionsHistory = {
  setGenerationGeno: (data: IGeneration | null): SetGenerationGeno => ({
    type: HistoryActionsEnum.GENERATION_GENO,
    data,
  }),
  setGenerationGenoLoading: (data: boolean): SetGenerationGenoLoading => ({
    type: HistoryActionsEnum.GENERATION_GENO_LOADING,
    data,
  }),
  setGenerationPheno: (data: IGeneration | null): SetGenerationPheno => ({
    type: HistoryActionsEnum.GENERATION_PHENO,
    data,
  }),
  setGenerationPhenoLoading: (data: boolean): SetGenerationPhenoLoading => ({
    type: HistoryActionsEnum.GENERATION_PHENO_LOADING,
    data,
  }),
  setGenerationType: (data: GenerationType): SetGenerationType => ({
    type: HistoryActionsEnum.GENERATION_TYPE,
    data,
  }),
  setHistory: (data: IHistoryGraph | null): SetHistory => ({
    type: HistoryActionsEnum.HISTORY,
    data,
  }),
  setHistoryLoading: (data: boolean): SetHistoryLoading => ({
    type: HistoryActionsEnum.HISTORY_LOADING,
    data,
  }),
  setModalOpen: (data: boolean): SetModalOpen => ({
    type: HistoryActionsEnum.MODAL_OPEN,
    data,
  }),
  setModalPipeline: (
    data: IHistoryNodeIndividual | null
  ): SetModalPipeline => ({
    type: HistoryActionsEnum.MODAL_PIPELINE,
    data,
  }),
  setModalPipelineImage: (
    data: IPipelineImage | null
  ): SetModalPipelineImage => ({
    type: HistoryActionsEnum.MODAL_PIPELINE_IMAGE,
    data,
  }),
  setModalPipelineImageLoading: (
    data: boolean
  ): SetModalPipelineImageLoading => ({
    type: HistoryActionsEnum.MODAL_PIPELINE_IMAGE_LOADING,
    data,
  }),
};

export const closeHistoryModal = (): ThunkType => (dispatch) => {
  dispatch(actionsHistory.setModalOpen(false));
};

export const openHistoryModal =
    (individual: IHistoryNodeIndividual): ThunkTypeAsync =>
        async (dispatch) => {
            dispatch(actionsHistory.setModalPipeline(individual));
            dispatch(actionsHistory.setModalPipelineImageLoading(true));
            dispatch(actionsHistory.setModalOpen(true));
            try {
                const res = await pipelineAPI.getPipelineImage(individual.individual_id);
                dispatch(actionsHistory.setModalPipelineImage(res));
            } catch (error) {
                dispatch(actionsHistory.setModalPipelineImage(null));
                console.log(error);
    } finally {
      dispatch(actionsHistory.setModalPipelineImageLoading(false));
    }
  };

export const getGenerationGeno =
  (caseId: string): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsHistory.setGenerationGenoLoading(true));
    try {
      const geno = await analyticsAPI.getGenerations(caseId, "geno");
      dispatch(actionsHistory.setGenerationGeno(geno));
    } catch (error) {
      dispatch(actionsHistory.setGenerationGeno(null));
      console.log(error);
    } finally {
      dispatch(actionsHistory.setGenerationGenoLoading(false));
    }
  };

export const getGenerationPheno =
  (caseId: string): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsHistory.setGenerationPhenoLoading(true));
    try {
      const geno = await analyticsAPI.getGenerations(caseId, "pheno");
      dispatch(actionsHistory.setGenerationPheno(geno));
    } catch (error) {
      dispatch(actionsHistory.setGenerationPheno(null));
      console.log(error);
    } finally {
      dispatch(actionsHistory.setGenerationPhenoLoading(false));
    }
  };

export const getHistory =
  (caseId: string): ThunkTypeAsync =>
  async (dispatch) => {
    dispatch(actionsHistory.setHistoryLoading(true));
    try {
      const history = await composerAPI.getHistoryGraph(caseId);
      dispatch(actionsHistory.setHistory(history));
    } catch (error) {
      dispatch(actionsHistory.setHistory(null));
      console.log(error);
    } finally {
      dispatch(actionsHistory.setHistoryLoading(false));
    }
  };

export const setGenerationType =
  (type: GenerationType): ThunkType =>
  (dispatch) => {
    dispatch(actionsHistory.setGenerationType(type));
  };

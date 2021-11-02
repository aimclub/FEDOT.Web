import { showCasesAPI } from "../../API/showcase/showcaseAPI";
import { ICase, ICaseItem } from "../../API/showcase/showcaseInterface";
import {
  CaseActionsEnum,
  SetAllCases,
  SetLoadingCase,
  SetShowCase,
  ThunkTypeAsync,
} from "./showCase-types";

export const actionsCase = {
  setAllCases: (data: ICaseItem[]): SetAllCases => ({
    type: CaseActionsEnum.ALL_CASES,
    data,
  }),
  setLoadingCase: (data: boolean): SetLoadingCase => ({
    type: CaseActionsEnum.LOADING_CASE,
    data,
  }),
  setShowCase: (data: ICase | null): SetShowCase => ({
    type: CaseActionsEnum.SHOW_CASE,
    data,
  }),
};

export const getAllShowCases = (): ThunkTypeAsync => {
  return async (dispatch) => {
    try {
      const showCases = await showCasesAPI.getAllShowCases();
      dispatch(actionsCase.setAllCases(showCases));
    } catch (error) {
      dispatch(actionsCase.setAllCases([]));
      console.error(error);
    }
  };
};

export const getShowCase = (caseId: string): ThunkTypeAsync => {
  return async (dispatch) => {
    dispatch(actionsCase.setLoadingCase(true));
    try {
      const showcase = await showCasesAPI.getShowCase(caseId);
      dispatch(actionsCase.setShowCase(showcase));
    } catch (error) {
      console.error(error);
      dispatch(actionsCase.setShowCase(null));
    } finally {
      dispatch(actionsCase.setLoadingCase(false));
    }
  };
};

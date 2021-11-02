import { ICase, ICaseItem } from "../../API/showcase/showcaseInterface";
import { AllTypes, CaseActionsEnum, InitialStateType } from "./showCase-types";

export const initialState = {
  allCases: [] as ICaseItem[],
  isLoadingCase: false,
  showCase: null as ICase | null,
};

const caseReducer = (
  state = initialState,
  action: AllTypes
): InitialStateType => {
  switch (action.type) {
    case CaseActionsEnum.ALL_CASES:
      return { ...state, allCases: action.data };

    case CaseActionsEnum.LOADING_CASE:
      return { ...state, isLoadingCase: action.data };

    case CaseActionsEnum.SHOW_CASE:
      return { ...state, showCase: action.data };

    default:
      return state;
  }
};

export default caseReducer;

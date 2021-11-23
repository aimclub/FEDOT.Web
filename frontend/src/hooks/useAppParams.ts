import { useParams } from "react-router";

interface ParamTypes {
  caseId: string;
}

export const useAppParams = () => useParams<ParamTypes>();

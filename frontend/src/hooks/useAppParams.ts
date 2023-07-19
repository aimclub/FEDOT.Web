import { useParams } from "react-router-dom";

export const useAppParams = () => useParams<"caseId">();

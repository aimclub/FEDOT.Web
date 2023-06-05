import { useMemo } from "react";

import { metaAPI } from "../API/meta/metaAPI";
import { sandboxAPI } from "../API/sanbox/sandboxAPI";
import { useAppParams } from "./useAppParams";
import { IModelName } from "../API/meta/metaInterface";

export const useGetNodeDisplayNames: (initialDisplayName?: string) => {
  displayNames: {
    id: string;
    name: string;
  }[];
  modelNames: IModelName[] | undefined;
} = (initialDisplayName = "") => {
  const { caseId } = useAppParams();
  const { data: caseParams } = sandboxAPI.useGetSandboxParamsQuery(
    { caseId: caseId || "" },
    { skip: !caseId }
  );
  const { data: modelNames } = metaAPI.useGetAllModelNameQuery(
    { taskId: caseParams?.task_id || "" },
    { skip: !caseParams }
  );

  const displayNames = useMemo(
    () =>
      modelNames?.map((n) => ({
        id: n.display_name,
        name: n.display_name,
      })) || [{ id: initialDisplayName, name: initialDisplayName }],
    [modelNames, initialDisplayName]
  );

  return {
    displayNames,
    modelNames,
  };
};

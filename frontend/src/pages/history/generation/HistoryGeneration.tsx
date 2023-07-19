import scss from "./historyGeneration.module.scss";

import { useState } from "react";

import { analyticsAPI } from "../../../API/analytics/analyticsAPI";
import { GenerationType } from "../../../API/analytics/analyticsInterface";
import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import { useAppParams } from "../../../hooks/useAppParams";
import { cl } from "../../../utils/classnames";
import HistoryGenerationBoxplot from "./boxplot/HistoryGenerationBoxplot";

const BUTTONS: { name: string; type: GenerationType }[] = [
  {
    name: "Phenothypic convergence",
    type: "pheno",
  },
  { name: "Genotypic convergence", type: "geno" },
];

const HistoryGeneration = () => {
  const [generationType, setGenerationType] = useState<GenerationType>("pheno");
  const { caseId } = useAppParams();
  const { isFetching, data, isError } = analyticsAPI.useGetGenerationsQuery(
    { caseId: caseId || "", type: generationType },
    { skip: !caseId }
  );

  return (
    <section className={scss.root}>
      <div className={scss.tabs}>
        {BUTTONS.map((item) => (
          <button
            type="button"
            key={item.type}
            className={cl(
              scss.tab,
              item.type === generationType && scss.active
            )}
            onClick={() => setGenerationType(item.type)}
          >
            <span>{item.name}</span>
          </button>
        ))}
      </div>

      <div className={scss.content}>
        {isFetching ? (
          <AppLoader />
        ) : (
          <HistoryGenerationBoxplot generation={isError ? undefined : data} />
        )}
      </div>
    </section>
  );
};

export default HistoryGeneration;

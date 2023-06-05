import { FC, memo } from "react";

import { analyticsAPI } from "../../../../API/analytics/analyticsAPI";
import AppLoader from "../../../../components/UI/loaders/app/AppLoader";
import { useAppParams } from "../../../../hooks/useAppParams";
import SandboxChartsMetricData from "./data/SandboxChartsMetricData";

const SandboxChartsMetric: FC<{
  classes: Record<"chart" | "null" | "axis" | "mark", string>;
}> = ({ classes }) => {
  const { caseId } = useAppParams();
  const { data, isFetching } = analyticsAPI.useGetCaseMetricQuery(
    { caseId: caseId || "" },
    { skip: !caseId }
  );

  return (
    <div className={classes.chart}>
      {isFetching ? (
        <AppLoader />
      ) : data ? (
        <SandboxChartsMetricData metric={data} classes={classes} />
      ) : (
        <p className={classes.null}>no data</p>
      )}
    </div>
  );
};

export default memo(SandboxChartsMetric);

import { FC, memo } from "react";

import { analyticsAPI } from "../../../../API/analytics/analyticsAPI";
import { IResult } from "../../../../API/analytics/analyticsInterface";
import AppLoader from "../../../../components/UI/loaders/app/AppLoader";
import { useAppSelector } from "../../../../hooks/redux";
import { useAppParams } from "../../../../hooks/useAppParams";
import SandboxChartsResultLine from "./line/SandboxChartsResultLine";
import SandboxChartsResultScatter from "./scatter/SandboxChartsResultScatter";

const checkIsLineChart = (data: IResult): data is IResult<"line"> =>
  data.options.chart.type === "line";
const checkIsScatterChart = (data: IResult): data is IResult<"scatter"> =>
  data.options.chart.type === "scatter";

const SandboxChartsResult: FC<{
  classes: Record<"chart" | "null" | "axis" | "mark", string>;
}> = ({ classes }) => {
  const { caseId } = useAppParams();
  const { pipeline_uid } = useAppSelector((state) => state.sandbox);

  const { data, isFetching } = analyticsAPI.useGetPipelineResultQuery(
    { caseId: caseId || "", pipeline_uid },
    { skip: !caseId || !pipeline_uid }
  );

  return (
    <div className={classes.chart}>
      {!pipeline_uid ? (
        <></>
      ) : isFetching ? (
        <AppLoader />
      ) : data ? (
        checkIsLineChart(data) ? (
          <SandboxChartsResultLine result={data} classes={classes} />
        ) : checkIsScatterChart(data) ? (
          <SandboxChartsResultScatter result={data} classes={classes} />
        ) : (
          <p className={classes.null}>wront type</p>
        )
      ) : (
        <p className={classes.null}>no data</p>
      )}
    </div>
  );
};

export default memo(SandboxChartsResult);

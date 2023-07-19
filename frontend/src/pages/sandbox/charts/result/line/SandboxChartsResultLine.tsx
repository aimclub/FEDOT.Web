import { FC, memo } from "react";

import { ApexOptions } from "apexcharts";
import ReactApexChart from "react-apexcharts";

import { IResult } from "../../../../../API/analytics/analyticsInterface";

const SandboxChartsResultLine: FC<{
  result: IResult<"line">;
  classes: Record<"axis" | "mark", string>;
}> = ({ result, classes }) => {
  const options: ApexOptions = {
    chart: {
      type: "line",
      zoom: {
        enabled: true,
        type: "xy",
      },
    },
    dataLabels: {
      enabled: false,
    },
    stroke: {
      curve: "straight",
    },
    legend: {
      fontWeight: 400,
      fontFamily: "'Open sans'",
      fontSize: "12px",
    },
    colors: ["#2196F3", "#94CE45", "#FF9800", "#464646"], // цвета линий
    grid: {
      row: {
        colors: ["#f3f3f3", "transparent"],
        opacity: 0.5,
      },
    },
    xaxis: {
      ...result?.options.xaxis,
      title: {
        ...result?.options.xaxis.title,
        style: { cssClass: classes.axis }, // стиль названия оси X
      },
      labels: {
        style: { cssClass: classes.mark }, // стиль меток оси X
      },
    },
    yaxis: [
      {
        ...result?.options.yaxis,
        title: {
          ...result?.options?.yaxis?.title,
          style: { cssClass: classes.axis }, // стиль названия оси Y
        },
        labels: {
          style: { cssClass: classes.mark }, // стиль меток оси Y
        },
      },
    ],
  };

  return (
    <ReactApexChart
      options={options}
      series={result?.series}
      type="line"
      height={"100%"}
      width={"100%"}
    />
  );
};

export default memo(SandboxChartsResultLine);

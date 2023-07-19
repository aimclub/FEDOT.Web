import { FC, memo } from "react";

import { ApexOptions } from "apexcharts";
import ReactApexChart from "react-apexcharts";

import { IMetric } from "../../../../../API/analytics/analyticsInterface";

const SandboxChartsMetricData: FC<{
  metric: IMetric;
  classes: Record<"axis" | "mark", string>;
}> = ({ metric, classes }) => {
  const options: ApexOptions = {
    chart: {
      type: "line",
      zoom: {
        enabled: false,
      },
    },
    colors: ["#94CE45", "#464646"], // цвета линий
    dataLabels: {
      enabled: false,
    },
    stroke: {
      curve: "straight",
    },
    grid: {
      row: {
        colors: ["#f3f3f3", "transparent"], // takes an array which will be repeated on columns
        opacity: 0.5,
      },
    },
    xaxis: {
      ...metric?.options.xaxis,
      title: {
        ...metric?.options.xaxis.title,
        style: { cssClass: classes.axis }, // стиль названия оси X
      },
      labels: {
        style: { cssClass: classes.mark }, // стиль меток оси X
      },
    },
    yaxis: [
      {
        ...metric?.options?.yaxis,
        title: {
          ...metric?.options?.yaxis?.title,
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
      series={metric?.series}
      height={"100%"}
      width={"100%"}
    />
  );
};

export default memo(SandboxChartsMetricData);

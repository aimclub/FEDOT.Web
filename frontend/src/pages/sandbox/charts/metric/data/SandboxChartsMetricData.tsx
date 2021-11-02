import { ApexOptions } from "apexcharts";
import React, { FC, memo } from "react";
import ReactApexChart from "react-apexcharts";
import { useSelector } from "react-redux";

import { StateType } from "../../../../../redux/store";

const styles = {
  axis: {
    fontWeight: 700,
    fontFamily: "'Open Sans'",
    fontSize: "12px",
  },
  mark: {
    fontWeight: 400,
    fontFamily: "'Open Sans'",
    fontSize: "10px",
  },
};

const SandboxChartsMetricData: FC = () => {
  const { metric } = useSelector((state: StateType) => state.sandbox);

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
        style: styles.axis, // стиль названия оси X
      },
      labels: {
        style: styles.mark, // стиль меток оси X
      },
    },
    yaxis: [
      {
        ...metric?.options?.yaxis,
        title: {
          ...metric?.options?.yaxis?.title,
          style: styles.axis, // стиль названия оси Y
        },
        labels: {
          style: styles.mark, // стиль меток оси Y
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

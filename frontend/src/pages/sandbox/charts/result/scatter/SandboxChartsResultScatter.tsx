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
  legend: {
    fontWeight: 400,
    fontFamily: "'Open Sans'",
    fontSize: "12px",
  },
};

const SandboxChartsResultScatter: FC = () => {
  const { result } = useSelector((state: StateType) => state.sandbox);

  const options: ApexOptions = {
    chart: {
      type: "scatter",
      zoom: {
        enabled: true,
        type: "xy",
      },
    },
    legend: styles.legend,
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
        style: styles.axis, // стиль названия оси X
      },
      labels: {
        style: styles.mark, // стиль меток оси X
      },
    },
    yaxis: [
      {
        ...result?.options.yaxis,
        title: {
          ...result?.options?.yaxis?.title,
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
      series={result?.series}
      type="scatter"
      height={"100%"}
      width={"100%"}
    />
  );
};

export default memo(SandboxChartsResultScatter);

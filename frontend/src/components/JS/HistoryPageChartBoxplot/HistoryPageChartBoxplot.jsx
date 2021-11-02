import React, { memo } from "react";
import Plot from "react-plotly.js";

const HistoryPageChartBoxplot = ({ data }) => {
  return (
    <Plot
      data={data.reverse()}
      layout={{
        margin: { t: 20, b: 30 },
        height: 150 + 40 * data.length,
        width: "370",
        showlegend: false,
        yaxis: { fixedrange: true },
        xaxis: {
          fixedrange: true,
          rangemode: "normal",
        },
      }}
      config={{
        moauseZoom: false,
        displayModeBar: false,
        showlegend: true,
      }}
    />
  );
};

export default memo(HistoryPageChartBoxplot);

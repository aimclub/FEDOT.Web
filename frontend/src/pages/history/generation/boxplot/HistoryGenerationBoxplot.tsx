import scss from "./historyGenerationBoxplot.module.scss";

import { FC, memo, useMemo } from "react";

import type { BoxPlotData } from "plotly.js";
import Plot from "react-plotly.js";

import { IGeneration } from "../../../../API/analytics/analyticsInterface";

const HistoryGenerationBoxplot: FC<{
  generation?: IGeneration;
}> = ({ generation }) => {
  const data = useMemo<Partial<BoxPlotData>[]>(
    () =>
      generation?.series
        .slice()
        .reverse()
        .map((i) => ({ ...i, name: `${i.name} epoch` })) || [],

    [generation]
  );

  return generation ? (
    <Plot
      data={data}
      layout={{
        margin: { t: 20, b: 40, l: 80, r: 24 },
        width: 412,
        height: 150 + 40 * data.length,
        showlegend: false,
        yaxis: { fixedrange: true },
        xaxis: { fixedrange: true, rangemode: "normal" },
      }}
      config={{
        displayModeBar: false,
      }}
    />
  ) : (
    <p className={scss.empty}>no data</p>
  );
};

export default memo(HistoryGenerationBoxplot);

import React, { FC, memo, useEffect, useState } from "react";

import { makeStyles } from "@material-ui/core/styles";

import {
  IGeneration,
  IGenerationSeries,
} from "../../../../API/analytics/analyticsInterface";
import HistoryPageChartBoxplot from "../../../../components/JS/HistoryPageChartBoxplot/HistoryPageChartBoxplot";

const useStyles = makeStyles(() => ({
  empty: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 300,
    fontSize: 24,
    lineHeight: "100%",
    textAlign: "center",

    color: "#cfd8dc",
  },
}));

export const editArr = (arr: IGenerationSeries[]) =>
  arr.map((item) => ({ ...item, name: `${+item.name} epoch` }));

interface I {
  generation: IGeneration | null;
}

const HistoryGenerationBoxplot: FC<I> = ({ generation }) => {
  const classes = useStyles();

  const [data, setData] = useState<IGenerationSeries[]>([]);

  useEffect(() => {
    if (!!generation) {
      setData(editArr(generation.series));
    }
  }, [generation]);

  return !!generation ? (
    <HistoryPageChartBoxplot data={data} />
  ) : (
    <p className={classes.empty}>no data</p>
  );
};

export default memo(HistoryGenerationBoxplot);

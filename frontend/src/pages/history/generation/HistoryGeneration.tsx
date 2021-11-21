import React, { FC, memo } from "react";
import { useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import AppLoader from "../../../components/UI/loaders/AppLoader";
import { StateType } from "../../../redux/store";
import HistoryGenerationBoxplot from "./boxplot/HistoryGenerationBoxplot";
import HistoryGenerationType from "./type/HistoryGenerationType";

const useStyles = makeStyles(() => ({
  root: {
    padding: 25,
    width: 420,
    boxSizing: "border-box",

    background: "#FFFFFF",
    borderRadius: 8,
  },
  content: {
    minHeight: 200,
    height: "calc(100% - 70px)",

    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
}));

const HistoryGeneration: FC = () => {
  const classes = useStyles();

  const {
    isLoadingGenerationGeno,
    isLoadingGenerationPheno,
    generationType,
    generationGeno,
    generationPheno,
  } = useSelector((state: StateType) => state.history);

  return (
    <section className={classes.root}>
      <HistoryGenerationType />
      <div className={classes.content}>
        {(generationType === "geno" && isLoadingGenerationGeno) ||
        (generationType === "pheno" && isLoadingGenerationPheno) ? (
          <AppLoader />
        ) : (
          <HistoryGenerationBoxplot
            generation={
              generationType === "geno"
                ? generationGeno
                : generationType === "pheno"
                ? generationPheno
                : null
            }
          />
        )}
      </div>
    </section>
  );
};

export default memo(HistoryGeneration);

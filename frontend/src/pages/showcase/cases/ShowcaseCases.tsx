import { Fade } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC, memo } from "react";
import { useSelector } from "react-redux";
import Title from "../../../components/Title/Title";
import { StateType } from "../../../redux/store";
import ShowcaseCasesCard from "./ShowcaseCasesCard";

const useStyles = makeStyles(() => ({
  root: {
    padding: 24,

    borderRadius: 8,
    backgroundColor: "#ffffff",

    transition: "all 3s",
  },
  cases: {
    marginTop: 20,

    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(388px, 1fr))",
    gap: 16,
    alignItems: "center",
    justifyItems: "center",
  },
}));

const ShowcaseCases: FC = () => {
  const classes = useStyles();

  const { allCases } = useSelector((state: StateType) => state.showCase);

  return (
    <Fade in={!!allCases} mountOnEnter unmountOnExit timeout={2000}>
      <section className={classes.root}>
        <Title name="Case" type="h2" />
        <div className={classes.cases}>
          {allCases.map((caseItem) => (
            <ShowcaseCasesCard key={caseItem.case_id} data={caseItem} />
          ))}
        </div>
      </section>
    </Fade>
  );
};

export default memo(ShowcaseCases);

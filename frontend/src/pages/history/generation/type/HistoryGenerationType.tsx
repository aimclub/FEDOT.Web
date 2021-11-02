import { makeStyles } from "@material-ui/core/styles";
import React, { FC, memo } from "react";
import { useDispatch, useSelector } from "react-redux";
import { GenerationType } from "../../../../API/analytics/analyticsInterface";
import { setGenerationType } from "../../../../redux/history/history-actions";
import { StateType } from "../../../../redux/store";

const useStyles = makeStyles(() => ({
  root: {
    paddingBottom: 24,

    borderBottom: "1px solid #C4C4C4",

    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },

  button: {
    margin: 0,
    padding: "0 15px",
    width: "100%",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 18,
    lineHeight: "120%",
    letterSpacing: "0.15px",

    outline: "none",
    border: 0,
    borderRadius: 0,
    backgroundColor: "transparent",

    "&:not(:first-child)": {
      borderLeft: "1px solid #C4C4C4",
    },
  },
  active: {
    fontWeight: 700,
  },
  notActive: {
    cursor: "pointer",
    "&:hover": {
      borderRadius: 8,
      background: "#E2E7EA",

      transition: "all 0.5s",
    },
  },
}));

interface IButton {
  name: string;
  type: GenerationType;
}

const HistoryGenerationType: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { generationType } = useSelector((state: StateType) => state.history);

  const toggleGenerationType = (type: GenerationType) => {
    dispatch(setGenerationType(type));
  };

  const buttons: IButton[] = [
    {
      name: "Phenothypic convergence",
      type: "pheno",
    },
    { name: "Genotypic convergence", type: "geno" },
  ];

  return (
    <div className={classes.root}>
      {buttons.map((btn) => (
        <button
          type="button"
          key={btn.type}
          className={`${classes.button} ${
            generationType === btn.type ? classes.active : classes.notActive
          }`}
          onClick={() => toggleGenerationType(btn.type)}
        >
          <span>{btn.name}</span>
        </button>
      ))}
    </div>
  );
};

export default memo(HistoryGenerationType);

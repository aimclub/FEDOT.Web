import React, { FC, memo, ReactNode } from "react";

import { makeStyles } from "@material-ui/core/styles";
import { Button } from "@material-ui/core";

const useStyles = makeStyles(() => ({
  root: {
    minHeight: 48,
    width: "100%",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 16,
    lineHeight: "120%",
    textAlign: "center",
    textTransform: "none",

    borderRadius: "4px",
    background: "#263238",
    color: "#ffffff",

    "&:disabled": {
      background: "#ECEFF1",
    },
    "&:hover": {
      background: "#515B5F",
    },
  },
}));

interface I {
  children: ReactNode;
  disabled?: boolean;
  className?: string;
}

const SignInButonSubmit: FC<I> = ({ children, disabled, className }) => {
  const classes = useStyles();

  return (
    <Button
      className={`${classes.root} ${className}`}
      type="submit"
      disabled={disabled}
    >
      {children}
    </Button>
  );
};

export default memo(SignInButonSubmit);

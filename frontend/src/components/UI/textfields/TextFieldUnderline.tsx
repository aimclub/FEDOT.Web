import React, { ChangeEventHandler, FC } from "react";

import { TextField } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles(() => ({
  root: {
    "& .MuiInput-root": {},
    "& .MuiInput-root:focus": {
      background: "transparent",
    },
    "& .MuiInput-underline:before": {
      borderBottom: "1px solid #B0BEC5",
    },
    "& .MuiInput-underline.Mui-disabled:before": {
      borderBottom: "1px solid #F2F2F2",
    },
    "& .MuiInput-underline.Mui-focused:before": {
      borderBottom: "1px solid #263238",
    },
    "& .MuiInput-underline:hover:not(.Mui-disabled):before": {
      borderBottom: "1px solid #263238",
    },
    "& .MuiInput-underline:after": {
      border: 0,
    },
    "& .MuiInput-input": {
      margin: 0,
      padding: "4px 0",

      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 14,
      lineHeight: "120%",
      letterSpacing: "0.15px",
      textOverflow: "ellipsis",
      overflow: "hidden",
    },
  },
}));

interface I {
  name: string;
  value: any;
  onChange?: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
  disabled?: boolean;
  className?: string;
}

const TextFieldUnderline: FC<I> = ({
  name,
  value,
  onChange,
  disabled,
  className,
}) => {
  const classes = useStyles();
  return (
    <TextField
      name={name}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={`${classes.root} ${className}`}
    ></TextField>
  );
};

export default TextFieldUnderline;

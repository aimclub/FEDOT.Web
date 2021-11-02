import React, { ChangeEventHandler, FC } from "react";

import { TextField } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles(() => ({
  root: {
    margin: "0 0 14px 0",
    color: "#000",
    // outlined
    "& .MuiOutlinedInput-notchedOutline": {
      border: "1px solid #B0BEC5", // default
    },
    "& .Mui-focused .MuiOutlinedInput-notchedOutline": {
      border: "1px solid #78909C", // focused
    },
    "&:hover :not(.Mui-disabled):not(.Mui-focused) .MuiOutlinedInput-notchedOutline":
      {
        border: "1px solid #90A4AE", // hover
      },
    "& .Mui-disabled .MuiOutlinedInput-notchedOutline": {
      border: "1px solid #ECEFF1", // disabled
    },
    // label
    "& .MuiInputLabel-root": {
      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 16,
      lineHeight: "120%",
      textTransform: "capitalize",
    },
    "& .MuiInputLabel-root:not(.Mui-error)": {
      color: "#B0BEC5",
    },
    "& .MuiInputLabel-root.Mui-focused:not(.Mui-error)": {
      color: "#78909C",
    },
    "& .MuiInputLabel-root.Mui-disabled": {
      color: "#ECEFF1",
    },
    // input
    "& .MuiOutlinedInput-input": {
      padding: "15px 22px",

      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 16,
      lineHeight: "120%",
    },
    "& .MuiInputLabel-root:not(.MuiInputLabel-shrink)": {
      transform: "translate(22px, 15px)",
    },
    "& .Mui-disabled.MuiOutlinedInput-input": {
      color: "#ECEFF1",
    },
    // helpText (error)
    "& .MuiFormHelperText-root": {
      margin: "4px 0 0 22px",
      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 12,
      lineHeight: "120%",
    },
  },
}));

interface I {
  name: string;
  label?: string;
  type?: "password" | "text";
  value: any;
  onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
  disabled?: boolean;
  className?: string;
  error?: string;
}

const TextFieldFormikSignIn: FC<I> = ({
  name,
  label,
  type,
  value,
  onChange,
  disabled,
  className,
  error,
}) => {
  const classes = useStyles();
  return (
    <TextField
      variant="outlined"
      className={`${classes.root} ${className}`}
      label={label || name}
      name={name}
      type={type}
      value={value}
      onChange={onChange}
      disabled={disabled}
      error={!!error}
      helperText={error || ""}
    />
  );
};

export default TextFieldFormikSignIn;

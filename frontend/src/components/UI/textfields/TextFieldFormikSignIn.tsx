import TextField from "@mui/material/TextField";
import { styled } from "@mui/material/styles";
import { ChangeEventHandler, FC, memo } from "react";

const CusstomTextField = styled(TextField)({
  margin: "0 0 14px 0",
  color: "#000",

  // outlined
  "& .MuiOutlinedInput-notchedOutline": {
    border: "1px solid #B0BEC5", // default
  },

  ".MuiInputBase-root": {
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
      border: "1px solid #78909C", // focused
    },

    "&:hover:not(.Mui-disabled):not(.Mui-focused) .MuiOutlinedInput-notchedOutline":
      {
        border: "1px solid #90A4AE", // hover
      },
    "&.Mui-disabled .MuiOutlinedInput-notchedOutline": {
      border: "1px solid #ECEFF1", // disabled
    },
  },

  // label
  "& .MuiInputLabel-root": {
    fontFamily: "'Open sans'",
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

    fontFamily: "'Open sans'",
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
    fontFamily: "'Open sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 12,
    lineHeight: "120%",
  },
});

const TextFieldFormikSignIn: FC<{
  name: string;
  label?: string;
  type?: "password" | "text";
  value: string | number;
  onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
  disabled?: boolean;
  className?: string;
  error?: string;
}> = ({ name, label, type, value, onChange, disabled, className, error }) => {
  return (
    <CusstomTextField
      variant="outlined"
      className={className}
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

export default memo(TextFieldFormikSignIn);

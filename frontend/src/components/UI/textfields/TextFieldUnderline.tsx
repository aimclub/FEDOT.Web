import TextField, { TextFieldProps } from "@mui/material/TextField";
import { styled } from "@mui/material/styles";

const TextFieldUnderline = styled((props: TextFieldProps) => (
  <TextField {...props} variant="standard" />
))({
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

    fontFamily: "'Open sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "120%",
    letterSpacing: "0.15px",
    textOverflow: "ellipsis",
    overflow: "hidden",
  },
});

export default TextFieldUnderline;

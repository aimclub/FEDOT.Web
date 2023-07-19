import { styled } from "@mui/material/styles";

import Button from "@mui/material/Button";

const SignInButonSubmit = styled(Button)({
  minHeight: 48,
  // width: "100%",

  fontFamily: "'Open sans'",
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
});

export default SignInButonSubmit;

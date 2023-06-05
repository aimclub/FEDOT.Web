import LinearProgress from "@mui/material/LinearProgress";
import { styled } from "@mui/material/styles";

const LinearLoader = styled(LinearProgress)({
  minHeight: 8,

  borderRadius: "99em",
  backgroundColor: "rgba(38, 50, 56, 0.4)",
  "& .MuiLinearProgress-bar": {
    maxWidth: "30%",

    borderRadius: "99em",
    backgroundColor: "#263238",
  },
});

export default LinearLoader;

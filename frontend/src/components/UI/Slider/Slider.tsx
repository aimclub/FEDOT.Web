import SliderMUI from "@mui/material/Slider";
import { styled } from "@mui/material/styles";

const Slider = styled(SliderMUI)({
  color: "#263238",

  "& .MuiSlider-rail": {
    width: "calc(100% + 8px)",
    height: 8,
    borderRadius: "99em",
  },

  "& .MuiSlider-track": {
    height: 8,
    borderRadius: "99em",
  },

  "& .MuiSlider-mark": {
    height: 8,
    width: 8,
    backgroundColor: "#ffffff",
    border: "1px solid #000",
    borderRadius: "99em",
  },

  "& .MuiSlider-thumb": {
    height: 24,
    width: 24,

    backgroundColor: "#ffffff",
    border: "2px solid currentColor",

    boxShadow: "none",
    "&:focus, &:hover, &:active, &.Mui-focusVisible": {
      boxShadow: "none",
    },
  },

  "& .MuiSlider-valueLabel": {
    padding: 0,
    width: 32,
    height: 32,

    borderRadius: "50% 50% 50% 0",
    backgroundColor: "#263238",
    color: "#ffffff",

    transformOrigin: "bottom left",
    transform: "translate(50%, calc(-50% - 8px)) rotate(-45deg) scale(0)",
    "&:before": { display: "none" },
    "&.MuiSlider-valueLabelOpen": {
      transform: "translate(50%, calc(-50% - 8px)) rotate(-45deg) scale(1)",
    },
    "& > *": {
      transform: "rotate(45deg)",
    },
  },
});

export default Slider;

import React from "react";
import { withStyles } from "@material-ui/core/styles";
import { Slider } from "@material-ui/core";

const CustomSlider = withStyles({
  root: {
    width: "558px",
    height: 8,
    position: "absolute",
    left: 200,
    top: 50,
    zIndex: 2,
  },
  thumb: {
    height: 24,
    width: 24,
    backgroundColor: "#fff",
    border: "2px solid currentColor",
    marginTop: -8,
    marginLeft: -12,
    "&:focus, &:hover, &$active": {
      boxShadow: "inherit",
    },
  },
  active: {},
  valueLabel: {
    left: "calc(-50% + 4px)",
  },
  track: {
    height: 8,
    borderRadius: 4,
  },
  rail: {
    height: 8,
    borderRadius: 4,
  },
})(Slider);

export default CustomSlider;

import { withStyles } from "@material-ui/core/styles";
import { Slider } from "@material-ui/core";

const CustomSlider = withStyles({
  root: {
    width: "558px",
    height: 8,
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
  },
  rail: {
    height: 8,
  },
  mark: {
    backgroundColor: "#fff",
    border: "1px solid #000",
    borderRadius: "50%",
    height: 8,
    width: 8,
    marginTop: -1,
  },
})(Slider);

export default CustomSlider;

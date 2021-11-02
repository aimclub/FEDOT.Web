import { withStyles } from "@material-ui/core/styles";

import Tooltip from "@material-ui/core/Tooltip";

const CustomTooltip = withStyles((theme) => ({
  tooltip: {
    margin: "30px 0 0",
  },
}))(Tooltip);

export default CustomTooltip;

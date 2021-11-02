import React, { FC } from "react";

import { makeStyles } from "@material-ui/core/styles";
import Loader from "react-loader-spinner";

export const useStyles = makeStyles(() => ({
  blackout: {
    width: "100%",
    height: "100%",

    borderRadius: 4,
    backgroundColor: "rgba(0, 0, 0, 0.5)",

    position: "absolute",
    top: 0,
    left: 0,
    zIndex: 1000,

    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
}));

interface I {
  hasBlackout?: boolean;
}

const AppLoader: FC<I> = ({ hasBlackout = false }) => {
  const classes = useStyles();

  return (
    <div className={hasBlackout ? classes.blackout : ""}>
      <Loader
        type="MutatingDots"
        color="#94CE45"
        secondaryColor="#263238"
        height={100}
        width={100}
      />
    </div>
  );
};

export default AppLoader;

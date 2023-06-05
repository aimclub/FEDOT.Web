import scss from "./appLoader.module.scss";

import { FC } from "react";
import { MutatingDots as Loader } from "react-loader-spinner";

import { cl } from "../../../../utils/classnames";

const AppLoader: FC<{ hasBlackout?: boolean; className?: string }> = ({
  hasBlackout = false,
  className,
}) => {
  return (
    <div className={cl(hasBlackout && scss.blackout, className)}>
      <Loader
        color="#94CE45"
        secondaryColor="#263238"
        height={100}
        width={100}
      />
    </div>
  );
};

export default AppLoader;

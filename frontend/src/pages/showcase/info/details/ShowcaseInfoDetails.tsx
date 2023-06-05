import scss from "./showcaseInfoDetails.module.scss";

import { FC } from "react";

import { cl } from "../../../../utils/classnames";
import CustomTooltip from "../../../../components/UI/tooltip/CustomTooltip";

const ShowcaseInfoDetails: FC<{
  className?: string;
  details: Record<string, number>;
}> = ({ details, className }) => {
  return (
    <div className={cl(scss.root, className)}>
      {Object.entries(details).map((metric) => (
        <CustomTooltip
          key={metric[0]}
          title={`${metric[0]}: ${metric[1]}`}
          placement="top"
          arrow
        >
          <div className={scss.item}>
            <p className={scss.metric}>{metric[0]}</p>
            <p className={scss.value}>{metric[1]}</p>
          </div>
        </CustomTooltip>
      ))}
    </div>
  );
};

export default ShowcaseInfoDetails;

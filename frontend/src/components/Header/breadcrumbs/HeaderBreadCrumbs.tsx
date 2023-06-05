import scss from "./headerBreadcrumbs.module.scss";

import { FC, Fragment, memo } from "react";

import GradientIcon from "@mui/icons-material/Gradient";
import { Link } from "react-router-dom";

import { cl } from "../../../utils/classnames";

export interface IBreadcrubs {
  name: string;
  Icon?: React.ComponentType<{ className?: string }>;
  crumbs?: { name: string; path: string }[];
}

const Breadcrumbs: FC<IBreadcrubs> = ({
  name,
  Icon = GradientIcon,
  crumbs,
}) => {
  return (
    <div className={scss.root}>
      <Icon className={scss.icon} />
      {crumbs?.map((item) => (
        <Fragment key={item.path}>
          <Link to={item.path} className={cl(scss.text, scss.link)}>
            {item.name}
          </Link>
          <span className={scss.text}>{"/"}</span>
        </Fragment>
      ))}
      <p className={scss.text}>{name}</p>
    </div>
  );
};

export default memo(Breadcrumbs);

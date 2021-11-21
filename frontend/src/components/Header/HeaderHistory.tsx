import React, { FC } from "react";
import { Link } from "react-router-dom";

import { Breadcrumbs } from "@material-ui/core";
import GradientIcon from "@material-ui/icons/Gradient";

import { useAppParams } from "../../hooks/useAppParams";
import { AppRoutesEnum } from "../../routes";
import scss from "./header.module.scss";

const HeaderHistory: FC = () => {
  const { caseId } = useAppParams();

  return (
    <div className={scss.nav}>
      <GradientIcon className={scss.icon} />
      <Breadcrumbs>
        <Link to={`${AppRoutesEnum.TO_SANDBOX}${caseId}`} className={scss.text}>
          Sandbox
        </Link>
        <p className={scss.text}>History</p>
      </Breadcrumbs>
    </div>
  );
};

export default HeaderHistory;

import React, { FC } from "react";

import style from "./header.module.scss";
import { Typography } from "@material-ui/core";

export interface IHeader {
  title: string;
  logo: any;
  subComponent?: any;
}

const Header: FC<IHeader> = (props) => {
  return (
    <div className={style.root}>
      <div className={style.logoText}>
        {props.logo}
        <Typography variant="subtitle2" className={style.title}>
          {props.title}
        </Typography>
      </div>
      <div>{props.subComponent}</div>
    </div>
  );
};
export default Header;

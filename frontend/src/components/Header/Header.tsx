import React, { ReactChild } from "react";

import style from "./header.module.scss";
import { Paper, Typography } from "@material-ui/core";

type HeaderProps = {
  title: string;
  logo?: ReactChild;
  subComponent?: ReactChild;
};

const Header = (props: HeaderProps) => {
  return (
    <Paper elevation={3} className={style.root}>
      <div className={style.logoText}>
        {props.logo}
        <Typography variant="subtitle2" className={style.title}>
          {props.title}
        </Typography>
      </div>
      <div>{props.subComponent}</div>
    </Paper>
  );
};
export default Header;

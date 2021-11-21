import React, { FC } from "react";
import { useSelector } from "react-redux";
import { Route, Switch } from "react-router-dom";

import GradientIcon from "@material-ui/icons/Gradient";
import SettingsIcon from "@material-ui/icons/Settings";
import TerrainIcon from "@material-ui/icons/Terrain";

import scss from "./header.module.scss";

import { StateType } from "../../redux/store";
import { AppRoutesEnum } from "../../routes";
import HeaderHistory from "./HeaderHistory";
import HeaderMenu from "./HeaderMenu";

const Header: FC = () => {
  const { isAuth } = useSelector((state: StateType) => state.auth);
  return (
    <div className={scss.root}>
      <Switch>
        <Route exact path={AppRoutesEnum.SHOWCASE}>
          <div className={scss.nav}>
            <GradientIcon className={scss.icon} />
            <p className={scss.text}>Showcase</p>
          </div>
        </Route>

        <Route exact path={AppRoutesEnum.SANDBOX}>
          <div className={scss.nav}>
            <TerrainIcon className={scss.icon} />

            <p className={scss.text}>Sandbox</p>
          </div>
        </Route>

        <Route exact path={AppRoutesEnum.HISTORY}>
          <HeaderHistory />
        </Route>

        <Route exact path={AppRoutesEnum.SETTING}>
          <div className={scss.nav}>
            <SettingsIcon className={scss.icon} />
            <p className={scss.text}>Setting</p>
          </div>
        </Route>
      </Switch>

      <div className={scss.container}>
        {/*<AddButton>Submit New Model</AddButton>*/}
        {!isAuth && <p className={scss.text}>not auth</p>}
        <div className={scss.line} />
        <HeaderMenu />
      </div>
    </div>
  );
};

export default Header;

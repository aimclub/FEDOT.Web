import React, { memo } from "react";
import { useSelector } from "react-redux";
import { Redirect, Route, Switch } from "react-router-dom";

import scss from "./workSpace.module.scss";

import HistoryPage from "../../pages/history/HistoryPage";
import SandboxPage from "../../pages/sandbox/SandboxPage";
import ShowcasePage from "../../pages/showcase/ShowcasePage";
import { StateType } from "../../redux/store";
import { AppRoutesEnum } from "../../routes";
import Header from "../Header/Header";
import LeftMenu from "../LeftMenu/LeftMenu";

const WorkSpace = () => {
  const { isAuth } = useSelector((state: StateType) => state.auth);

  return (
    <div className={scss.root}>
      <div className={scss.leftMenu}>
        <LeftMenu />
      </div>
      <header className={scss.header}>
        <Header />
      </header>
      <main className={scss.content}>
        <Switch>
          <Route path={AppRoutesEnum.SHOWCASE} component={ShowcasePage} />
          <Route exact path={AppRoutesEnum.SANDBOX} component={SandboxPage} />
          <Route exact path={AppRoutesEnum.HISTORY} component={HistoryPage} />
          {/* <Route exact path={AppRoutesEnum.SETTING} /> */}
          {isAuth ? <Redirect to={AppRoutesEnum.SHOWCASE} /> : <Redirect to={AppRoutesEnum.SIGNIN} />}
        </Switch>
      </main>
    </div>
  );
};

export default memo(WorkSpace);

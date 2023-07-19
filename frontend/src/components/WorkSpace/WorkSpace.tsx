import scss from "./workSpace.module.scss";

import { Outlet } from "react-router-dom";

import Header from "../Header/Header";
import LeftMenu from "../LeftMenu/LeftMenu";
import { Suspense } from "react";

const WorkSpace = () => {
  return (
    <div className={scss.root}>
      <LeftMenu className={scss.leftMenu} />
      <Header className={scss.header} />
      <main className={scss.content}>
        <Suspense>
          <Outlet />
        </Suspense>
      </main>
    </div>
  );
};

export default WorkSpace;

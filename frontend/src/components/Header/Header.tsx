import scss from "./header.module.scss";

import { FC } from "react";

import SettingsIcon from "@mui/icons-material/Settings";
import TerrainIcon from "@mui/icons-material/Terrain";
import { Route, Routes } from "react-router-dom";

import { useAppSelector } from "../../hooks/redux";
import { AppRoutesEnum } from "../../router/routes";
import { cl } from "../../utils/classnames";
import HeaderMenu from "./menu/HeaderMenu";
import HeaderBreadCrumbs from "./breadcrumbs/HeaderBreadCrumbs";

const Header: FC<{ className?: string }> = ({ className }) => {
  const { isAuth } = useAppSelector((state) => state.auth);

  return (
    <header className={cl(scss.root, className)}>
      <Routes>
        <Route
          path={AppRoutesEnum.SHOWCASE}
          element={<HeaderBreadCrumbs name="Showcase" />}
        />
        <Route path={`${AppRoutesEnum.SANDBOX}/${AppRoutesEnum.CASE}`}>
          <Route
            index
            element={<HeaderBreadCrumbs name="Sanbox" Icon={TerrainIcon} />}
          />
          <Route
            path={AppRoutesEnum.HISTORY}
            element={
              <HeaderBreadCrumbs
                name="History"
                crumbs={[{ name: "Sandbox", path: ".." }]}
              />
            }
          />
        </Route>
        <Route
          path={AppRoutesEnum.SETTING}
          element={<HeaderBreadCrumbs name="Setting" Icon={SettingsIcon} />}
        />
      </Routes>

      <div className={scss.container}>
        {/*<AddButton>Submit New Model</AddButton>*/}
        {!isAuth && <p className={scss.text}>not auth</p>}
        <div className={scss.line} />
        <HeaderMenu />
      </div>
    </header>
  );
};

export default Header;

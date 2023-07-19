import scss from "./leftMenu.module.scss";

import AccountTreeIcon from "@mui/icons-material/AccountTree";
import GradientIcon from "@mui/icons-material/Gradient";
import MenuIcon from "@mui/icons-material/Menu";
// import SettingsIcon from "@mui/icons-material/Settings";
import TerrainIcon from "@mui/icons-material/Terrain";
import { FC, useMemo } from "react";
import { NavLink } from "react-router-dom";

import Logo from "../../images/LogoMonochrome.svg";
import { GITHUB_LINK, goToPage } from "../../router/routes";
import { cl } from "../../utils/classnames";
import { useAppSelector } from "../../hooks/redux";

const LeftMenu: FC<{ className?: string }> = ({ className }) => {
  const { selected_showcase_id } = useAppSelector((state) => state.showcase);
  const navLinks = useMemo<
    {
      to: string;
      title: string;
      Icon: React.ComponentType<{ className: string }>;
      disabled?: boolean;
      target?: React.HTMLAttributeAnchorTarget;
      rel?: string;
    }[]
  >(
    () => [
      { to: goToPage.showcase, title: "Showcase", Icon: GradientIcon },

      {
        to: goToPage.sandbox(selected_showcase_id),
        title: "Sandbox",
        Icon: TerrainIcon,
      },
      // { to: GITHUB_LINK, title: "Settings", disabled: true },
      {
        to: GITHUB_LINK,
        title: "FEDOT",
        Icon: AccountTreeIcon,
        target: "_blank",
        rel: "noreferrer",
      },
    ],
    [selected_showcase_id]
  );

  return (
    <section className={cl(className, scss.root)}>
      <div className={scss.head}>
        <MenuIcon className={scss.icon} />
      </div>
      <div className={scss.menu}>
        <Logo className={scss.logo} />
        <ul className={scss.list}>
          {navLinks.map(({ title, to, Icon, disabled, ...props }, index) => (
            <NavLink
              {...props}
              to={to}
              key={index}
              className={({ isActive }) =>
                cl(
                  scss.link,
                  isActive && scss.active,
                  disabled && scss.disabled
                )
              }
            >
              <Icon className={scss.icon} />
              <span className={scss.title}>{title}</span>
            </NavLink>
          ))}
        </ul>
      </div>
    </section>
  );
};

export default LeftMenu;

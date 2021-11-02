import React, { FC } from "react";
import { NavLink } from "react-router-dom";

import { createStyles, makeStyles } from "@material-ui/core/styles";
import AccountTreeIcon from "@material-ui/icons/AccountTree";
import GradientIcon from "@material-ui/icons/Gradient";
import MenuIcon from "@material-ui/icons/Menu";
// import SettingsIcon from "@material-ui/icons/Settings";
import TerrainIcon from "@material-ui/icons/Terrain";

import scss from "./leftMenu.module.scss";

// import LogoMenu from "../../data/images/LogoMenu.png";
import Logo from "../../images/LogoMonochrome.svg";
import { AppRoutesEnum, GITHUB_LINK } from "../../routes";

const useStyles = makeStyles(() =>
  createStyles({
    icon: {
      width: 20,
      height: 20,

      color: "#FFFFFF",
    },
    button: {
      padding: "4px",
      width: "100%",
      boxSizing: "border-box",

      display: "flex",
      alignItems: "center",
      justifyContent: "center",

      textTransform: "none",
      textDecoration: "none",
      borderRadius: 0,
      color: "rgba(0, 0, 0, 0.87)",

      "&:disabled": {
        background: "#ECEFF1",
      },
      "&:hover": {
        background: "#B0BEC5",
      },
    },
    selected: {
      background: "#4F5B62",
    },
    text: {
      paddingLeft: 15,

      fontFamily: "Open Sans",

      fontSize: "14px",
      lineHeight: "150%",
      letterSpacing: "0.15px",

      transition: "all 1s",
      color: "#FFFFFF",
    },
    textHiden: {
      display: "hidden",

      transition: "all 1s",
    },
  })
);

const LeftMenu: FC = () => {
  const classes = useStyles();

  return (
    <section className={scss.root}>
      <div style={{ marginTop: 26 }}>
        <MenuIcon className={classes.icon} />
      </div>
      <div className={scss.line} />
      <img src={Logo} alt="Fedot" className={scss.logo} />
      <div className={scss.buttonsPosition}>
        <div className={scss.buttonWidth}>
          <NavLink
            className={classes.button}
            activeClassName={classes.selected}
            to={AppRoutesEnum.SHOWCASE}
          >
            <GradientIcon className={classes.icon} />
            <p className={scss.buttonText}>Showcase</p>
          </NavLink>
        </div>

        <div className={scss.buttonWidth}>
          <NavLink
            className={classes.button}
            activeClassName={classes.selected}
            to={AppRoutesEnum.SANDBOX}
          >
            <TerrainIcon className={classes.icon} />
            <p className={scss.buttonText}>Sandbox</p>
          </NavLink>
        </div>

        <div className={scss.buttonWidth}>
          <a
            className={classes.button}
            href={GITHUB_LINK}
            target="_blank"
            rel="noreferrer"
          >
            <AccountTreeIcon className={classes.icon} />
            <p className={scss.buttonText}>FEDOT</p>
          </a>
        </div>

        {/* <div className={scss.buttonWidth}>
          <NavLink
            className={classes.button}
            activeClassName={classes.selected}
            to={AppRoutesEnum.SETTING}
          >
            <SettingsIcon className={classes.icon} />
            <p className={scss.buttonText}>Settings</p>
          </NavLink>
        </div> */}
      </div>
      <div className={scss.line} />
    </section>
  );
};

export default LeftMenu;

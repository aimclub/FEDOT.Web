import React from "react";
import { useHistory } from "react-router-dom";

import {
  ClickAwayListener,
  Collapse,
  IconButton,
  MenuItem,
  MenuList,
  Paper,
} from "@material-ui/core";
import { createStyles, makeStyles, Theme } from "@material-ui/core/styles";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import ExitToAppIcon from "@material-ui/icons/ExitToApp";
// import SettingsIcon from "@material-ui/icons/Settings";

import { AppRoutesEnum } from "../../routes";
import { useDispatch } from "react-redux";
import { actionsAuth } from "../../redux/auth/auth-action";

interface IButton {
  name: string;
  action: (event?: React.MouseEvent<EventTarget>) => void;
  icon: React.ComponentType<any>;
}

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    button: {
      marginLeft: "10px",
      padding: 4,
      minWidth: "auto",
    },
    profileIcon: {
      width: 21,
      height: 21,
    },
    menu: {
      minWidth: 230,
      position: "absolute",
      top: "100%",
      right: 20,
      zIndex: 200,
    },
    menuPaper: {
      background: "#B0BEC5",
    },
    menuItem: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      "&:hover": {
        background: "#F2F2F2",
      },
      "&.Mui-focusVisible:not(:hover)": {
        background: "#CFD8DC",
      },
    },
    menuLabel: {
      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 14,
      lineHeight: "21px",
      letterSpacing: "0.15px",
      color: "#4f4f4f",
    },
    menuIcon: {
      height: 20,
      width: 20,
      color: "#4f4f4f",
    },
  })
);

const HeaderMenu = () => {
  const classes = useStyles();
  const history = useHistory();
  const [isOpen, setIsOpen] = React.useState(false);
  const dispatch = useDispatch();

  const handleToggle = (event: React.MouseEvent<EventTarget>) => {
    event.stopPropagation();
    setIsOpen((state) => !state);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  function handleListKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Tab") {
      event.preventDefault();
      setIsOpen(false);
    }
  }

  // const handleSettingClick = () => {
  //   handleClose();
  //   history.push(AppRoutesEnum.SETTING);
  // };

  const handleExitClick = () => {
    dispatch(actionsAuth.logOut());
    handleClose();
    history.push(AppRoutesEnum.SIGNIN);
  };

  // return focus to the button when we transitioned from !open -> open
  const prevOpen = React.useRef(isOpen);
  React.useEffect(() => {
    prevOpen.current = isOpen;
  }, [isOpen]);

  const buttons: IButton[] = [
    // { name: "Setting", action: handleSettingClick, icon: SettingsIcon },
    { name: "Exit", action: handleExitClick, icon: ExitToAppIcon },
  ];

  return (
    <>
      <IconButton className={classes.button} onClick={handleToggle}>
        <AccountCircleIcon className={classes.profileIcon} />
      </IconButton>

      {
        <Collapse in={isOpen} className={classes.menu}>
          <Paper className={classes.menuPaper}>
            <ClickAwayListener onClickAway={handleClose}>
              <MenuList autoFocusItem={isOpen} onKeyDown={handleListKeyDown}>
                {buttons.map((b, i) => (
                  <MenuItem
                    key={i}
                    className={classes.menuItem}
                    onClick={b.action}
                  >
                    <p className={classes.menuLabel}>{b.name}</p>
                    <b.icon className={classes.menuIcon} />
                  </MenuItem>
                ))}
              </MenuList>
            </ClickAwayListener>
          </Paper>
        </Collapse>
      }
    </>
  );
};

export default HeaderMenu;

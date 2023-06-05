import scss from "./headerMenu.module.scss";

import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import ExitToAppIcon from "@mui/icons-material/ExitToApp";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import MenuList from "@mui/material/MenuList";
import Paper from "@mui/material/Paper";
import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAppDispatch } from "../../../hooks/redux";
import { logout } from "../../../redux/auth/authSlice";
import { AppRoutesEnum } from "../../../router/routes";

const HeaderMenu = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [open, setOpen] = useState(false);

  const handleToggle = useCallback((event: React.MouseEvent<EventTarget>) => {
    event.stopPropagation();
    setOpen((prev) => !prev);
  }, []);

  const handleClose = useCallback(() => {
    setOpen(false);
  }, []);

  const handleListKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === "Tab") {
      event.preventDefault();
      setOpen(false);
    }
  }, []);

  const handleExitClick = useCallback(() => {
    dispatch(logout());
    handleClose();
    navigate(AppRoutesEnum.SIGNIN);
  }, [dispatch, handleClose, navigate]);

  return (
    <div className={scss.root}>
      <IconButton className={scss.button} onClick={handleToggle}>
        <AccountCircleIcon className={scss.icon} />
      </IconButton>

      <Collapse in={open} className={scss.menu}>
        <Paper className={scss.menuPaper}>
          <ClickAwayListener onClickAway={handleClose}>
            <MenuList autoFocusItem={open} onKeyDown={handleListKeyDown}>
              <MenuItem className={scss.menuItem} onClick={handleExitClick}>
                <p className={scss.menuLabel}>Exit</p>
                <ExitToAppIcon className={scss.icon} />
              </MenuItem>
            </MenuList>
          </ClickAwayListener>
        </Paper>
      </Collapse>
    </div>
  );
};

export default HeaderMenu;

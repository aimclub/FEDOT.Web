import React, { FC } from "react";
import clsx from "clsx";
import { makeStyles } from "@material-ui/core/styles";
import {
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from "@material-ui/core";
import SettingsIcon from "@material-ui/icons/Settings";
import GradientIcon from "@material-ui/icons/Gradient";
import TerrainIcon from "@material-ui/icons/Terrain";
import WidgetsIcon from "@material-ui/icons/Widgets";
import LogoFedot from "../Svg/LogoFedot";

const drawerWidth = 180;
const MENU_LINK = [
  { text: "Showcase", icon: <GradientIcon /> },
  { text: "Sandbox", icon: <TerrainIcon /> },
  { text: "FEDOT", icon: <WidgetsIcon /> },
];

const useStyles = makeStyles((theme) => ({
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: "nowrap",
    "& > *": {
      color: "#fff",
      overflowX: "hidden",
    },
  },
  drawerOpen: {
    backgroundColor: "#263238",
    width: drawerWidth,
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawerClose: {
    backgroundColor: "#263238",
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: "hidden",
    width: theme.spacing(7) + 1,
    [theme.breakpoints.up("sm")]: {
      width: theme.spacing(8) + 1,
    },
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
  },
  listItemIcon: {
    color: "#fff",
  },
  divider: { backgroundColor: "#fff" },
}));

export interface ISideMenu {
  changeTheme(): void;
}

const SideMenu: FC<ISideMenu> = ({ changeTheme }) => {
  const classes = useStyles();
  const [open, setOpen] = React.useState(false);

  const handleDrawerToggle = () => {
    setOpen(!open);
  };

  return (
    <Drawer
      variant="permanent"
      className={clsx(classes.drawer, {
        [classes.drawerOpen]: open,
        [classes.drawerClose]: !open,
      })}
      classes={{
        paper: clsx({
          [classes.drawerOpen]: open,
          [classes.drawerClose]: !open,
        }),
      }}
      onMouseEnter={handleDrawerToggle}
      onMouseLeave={handleDrawerToggle}
    >
      <div className={classes.toolbar}>
        <LogoFedot viewBox="0 0 269 329" style={{ fontSize: 40 }} />
      </div>
      <Divider className={classes.divider} />
      <List>
        {MENU_LINK.map((item, index) => (
          <ListItem button key={item.text}>
            <ListItemIcon className={classes.listItemIcon}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
      <div style={{ flexGrow: 1 }} />
      <ListItem button onClick={changeTheme}>
        <ListItemIcon className={classes.listItemIcon}>
          <SettingsIcon />
        </ListItemIcon>
        <ListItemText primary="Настройки" />
      </ListItem>
    </Drawer>
  );
};
export default SideMenu;

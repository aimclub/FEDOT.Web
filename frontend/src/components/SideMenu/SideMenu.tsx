import React, { useEffect, useMemo } from "react";
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
import GraphCreationList from "../GraphCreationList/GraphCreationList";
import ListItemLink from "../ListItemLink/ListItemLink";
import { useHistory } from "react-router-dom";

const drawerWidth = 180;
const MENU_LINK = [
  { text: "Showcase", icon: <GradientIcon />, to: "/" },
  { text: "Sandbox", icon: <TerrainIcon />, to: "/sandbox" },
  { text: "FEDOT", icon: <WidgetsIcon />, to: "/fedot" },
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

type SideMenuProps = {
  changeTheme(): void;
};

const SideMenu = ({ changeTheme }: SideMenuProps) => {
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
        <LogoFedot isLoading={false} />
      </div>
      <Divider className={classes.divider} />
      <List>
        {MENU_LINK.map((item, index) => (
          <ListItemLink
            to={item.to}
            key={item.text}
            icon={item.icon}
            primary={item.text}
          />
        ))}
      </List>
      <Divider className={classes.divider} />
      <GraphCreationList />
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

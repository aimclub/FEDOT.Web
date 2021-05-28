import React from "react";
import { ListItem, ListItemIcon, ListItemText } from "@material-ui/core";
import {
  Link as RouterLink,
  LinkProps as RouterLinkProps,
  useHistory,
} from "react-router-dom";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  list: {
    "&.MuiListItem-root.Mui-selected": {
      backgroundColor: "rgba(255, 255, 255, 0.16)",
    },
  },
}));

interface ListItemLinkProps {
  icon?: React.ReactElement;
  primary: string;
  to: string;
}

function ListItemLink(props: ListItemLinkProps) {
  const classes = useStyles();
  const history = useHistory();

  const { icon, primary, to } = props;

  const renderLink = React.useMemo(
    () =>
      React.forwardRef<any, Omit<RouterLinkProps, "to">>((itemProps, ref) => (
        <RouterLink to={to} ref={ref} {...itemProps} />
      )),
    [to]
  );
  return (
    <li>
      <ListItem
        className={classes.list}
        button
        selected={to === history.location.pathname}
        component={renderLink}
      >
        {icon ? (
          <ListItemIcon style={{ color: "#fff" }}>{icon}</ListItemIcon>
        ) : null}
        <ListItemText primary={primary} />
      </ListItem>
    </li>
  );
}

export default ListItemLink;

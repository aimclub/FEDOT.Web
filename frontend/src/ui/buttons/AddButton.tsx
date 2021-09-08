import React, {FC, memo, ReactNode} from "react";
import scss from "./addButon.module.scss";

import {createStyles, makeStyles} from "@material-ui/core/styles";
import {Button} from "@material-ui/core";
import AddIcon from "@material-ui/icons/Add";

const useStyles = makeStyles(() =>
    createStyles({
        button: {
            padding: "2px 4px 2px 0",
            textTransform: "none",
        },
        icon: {
            width: 18,
            height: 18,

            border: "1px solid #506072",
            borderRadius: 5,
        },
    })
);

interface IAddButton {
  onClick?(): void;
  children: ReactNode;
  disabled?: boolean;
}

const AddButton: FC<IAddButton> = ({ onClick, children, disabled }) => {
  const classes = useStyles();

  return (
    <div className={scss.root}>
      <Button className={classes.button} onClick={onClick} disabled={disabled}>
        <AddIcon className={classes.icon} />
        <p className={scss.text}>{children}</p>
      </Button>
    </div>
  );
};

export default memo(AddButton);

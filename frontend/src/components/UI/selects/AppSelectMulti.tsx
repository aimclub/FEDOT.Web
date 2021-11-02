import React, { FC } from "react";

import { Checkbox, FormControl, MenuItem, Select } from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles(() => ({
  root: {
    "& .MuiSelect-select": {
      padding: "4px 20px 4px 4px",
      fontFamily: "'Open Sans'",
      fontStyle: "normal",
      fontWeight: 400,
      fontSize: 14,
      lineHeight: "120%",
      letterSpacing: "0.15px",
      textOverflow: "ellipsis",
      overflow: "hidden",
    },
    "& .MuiSelect-select:focus": {
      background: "transparent",
    },
    "&.MuiInput-underline:before": {
      borderBottom: "1px solid #B0BEC5",
    },
    "&.MuiInput-underline.Mui-disabled:before": {
      borderBottom: "1px solid #F2F2F2",
    },
    "&.MuiInput-underline.Mui-focused:before": {
      borderBottom: "1px solid #263238",
    },
    "&.MuiInput-underline:hover:not(.Mui-disabled):before": {
      borderBottom: "1px solid #263238",
    },
    "&.MuiInput-underline:after": {
      border: 0,
    },
  },
  menuPaper: {
    maxHeight: 300,

    "&::-webkit-scrollbar": {
      width: 4,
    },
    "&::-webkit-scrollbar-track": {
      boxShadow: "inset 0 0 6px #263238",
      "-webkit-box-shadow": "inset 0 0 6px rgba(34, 60, 80, 0.2)",
      backgroundColor: "#CFD8DC",
      borderRadius: "0 4px 4px  0",
    },
    "&::-webkit-scrollbar-thumb": {
      borderRadius: 4,
      backgroundColor: "#546E7A",
    },
  },
  menuList: {
    padding: 0,
    width: "100%",
  },
  menuItem: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  menuItemValue: {
    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "120%",
    letterSpacing: "0.15px",
    textAlign: "center",
    flex: 1,
  },
  checkbox: {
    padding: 0,
    color: "#B0BEC5",
    "&.Mui-checked": {
      color: "#828282",
    },
  },
}));

interface I {
  name: string;
  currentValue: number[] | undefined;
  availableValues: {
    id: number;
    name: string;
  }[];
  onChange: (
    event: React.ChangeEvent<{ name?: string | undefined; value: unknown }>
  ) => void;
  disabled?: boolean;
  classname?: string;
}

const AppSelectMulti: FC<I> = ({
  name,
  currentValue,
  availableValues,
  onChange,
  disabled,
  classname,
}) => {
  const classes = useStyles();

  return (
    <FormControl className={classname}>
      <Select
        className={classes.root}
        multiple
        name={name}
        value={currentValue}
        renderValue={(selected) => (selected as string[]).join(", ")}
        onChange={onChange}
        disabled={disabled}
        MenuProps={{
          classes: { paper: classes.menuPaper, list: classes.menuList },
        }}
      >
        {availableValues &&
          availableValues.map((value) => (
            <MenuItem
              key={value.id}
              value={value.id}
              className={classes.menuItem}
            >
              <p className={classes.menuItemValue}>{value.name}</p>
              <Checkbox
                className={classes.checkbox}
                checked={
                  currentValue ? currentValue.indexOf(value.id) > -1 : false
                }
              />
            </MenuItem>
          ))}
      </Select>
    </FormControl>
  );
};

export default AppSelectMulti;

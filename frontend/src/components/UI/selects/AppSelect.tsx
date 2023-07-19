import { FC, memo } from "react";

import MenuItem from "@mui/material/MenuItem";
import Select, { SelectProps } from "@mui/material/Select";
import { styled } from "@mui/material/styles";

const CustomSelect = styled(Select)({
  "& .MuiSelect-select": {
    padding: "4px 20px 4px 4px",
    fontFamily: "'Open sans'",
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
  "&.MuiInput-underline.Mui-error:before": {
    borderBottom: "1px solid #FF0000",
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
});

const CustomMenuItem = styled(MenuItem)({
  fontFamily: "'Open sans'",
  fontStyle: "normal",
  fontWeight: 400,
  fontSize: 14,
  lineHeight: "120%",
  letterSpacing: "0.15px",
});

const AppSelect: FC<
  SelectProps & {
    availableValues: {
      id: string;
      name: string;
    }[];
  }
> = ({ availableValues, ...props }) => {
  return (
    <CustomSelect
      variant="standard"
      {...props}
      MenuProps={{
        sx: { maxHeight: 300 },
      }}
    >
      {availableValues.map((value) => (
        <CustomMenuItem key={value.id} value={value.id}>
          {value.name}
        </CustomMenuItem>
      ))}
    </CustomSelect>
  );
};

export default memo(AppSelect);

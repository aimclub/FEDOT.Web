import { FC, memo } from "react";

import Checkbox from "@mui/material/Checkbox";
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

const CustromMenuItem = styled(MenuItem)({
  display: "flex",
  alignItems: "center",

  fontFamily: "'Open sans'",
  fontStyle: "normal",
  fontWeight: 400,
  fontSize: 14,
  lineHeight: "120%",
  letterSpacing: "0.15px",
  textAlign: "center",
});

const CustomCheckbox = styled(Checkbox)({
  padding: 0,
  color: "#B0BEC5",
  "&.Mui-checked": {
    color: "#828282",
  },
});

const AppSelectMulti: FC<
  SelectProps & {
    availableValues: {
      id: number;
      name: string;
    }[];
  }
> = ({ value, availableValues, ...props }) => {
  return (
    <CustomSelect
      variant="standard"
      {...props}
      value={value}
      renderValue={(v) => (v as (string | number)[]).join(", ")}
      multiple
      MenuProps={{
        sx: { maxHeight: 300 },
      }}
    >
      {availableValues.map((item) => (
        <CustromMenuItem key={item.id} value={item.id}>
          <span style={{ flex: 1 }}>{item.name}</span>
          <CustomCheckbox
            checked={value ? (value as unknown[]).indexOf(item.id) >= 0 : false}
          />
        </CustromMenuItem>
      ))}
    </CustomSelect>
  );
};

export default memo(AppSelectMulti);

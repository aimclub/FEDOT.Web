import scss from "./pipelineNodeParamsFormItem.module.scss";

import { FC, memo, useCallback } from "react";

import CloseIcon from "@mui/icons-material/Close";
import IconButton from "@mui/material/IconButton";

import TextFieldUnderline from "../../../../UI/textfields/TextFieldUnderline";
import { cl } from "../../../../../utils/classnames";

const PipelineNodeParamsFormItem: FC<{
  className?: string;
  index: number;
  name: string;
  value: string | number | boolean;
  onChange(event: React.ChangeEvent<HTMLInputElement>): void;
  onDeleteParam(key: string): void;
}> = ({ className, index, name, value, onChange, onDeleteParam }) => {
  const handleDelete = useCallback(() => {
    onDeleteParam(name);
  }, [name, onDeleteParam]);

  return (
    <div className={cl(scss.root, className)}>
      <span>{index}</span>
      <span className={"classes.paramName"}>{name}</span>
      <TextFieldUnderline
        value={value}
        onChange={onChange}
        name={`node.params.${name}`}
      />
      <IconButton className={scss.icon} onClick={handleDelete}>
        <CloseIcon />
      </IconButton>
    </div>
  );
};

export default memo(PipelineNodeParamsFormItem);

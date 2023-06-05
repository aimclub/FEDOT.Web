import scss from "./sandboxPipelineButtons.module.scss";

import { FC, memo, useCallback } from "react";

import AddIcon from "@mui/icons-material/Add";
import AllInboxIcon from "@mui/icons-material/AllInbox";
import Button from "@mui/material/Button";

import { useAppDispatch } from "../../../../hooks/redux";
import { setPipelineNodeEdgesType } from "../../../../redux/sandbox/sandboxSlice";

const SandboxPipelineButtons: FC<{ disabled: boolean; onEvaluate(): void }> = ({
  disabled,
  onEvaluate,
}) => {
  const dispatch = useAppDispatch();

  const handleAddPointClick = useCallback(() => {
    dispatch(setPipelineNodeEdgesType("add"));
  }, [dispatch]);

  return (
    <div className={scss.root}>
      <Button className={scss.button} disabled={disabled} onClick={onEvaluate}>
        <AllInboxIcon className={scss.icon} />
        <span>Evaluate</span>
      </Button>

      <Button
        className={scss.button}
        onClick={handleAddPointClick}
        disabled={disabled}
      >
        <AddIcon className={scss.icon} />
        <span>add Point</span>
      </Button>
    </div>
  );
};

export default memo(SandboxPipelineButtons);

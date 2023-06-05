import scss from "./sandboxPipelineMenu.module.scss";

import { FC, memo, useCallback, useMemo } from "react";

import Button from "@mui/material/Button";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import Paper from "@mui/material/Paper";

import { useAppDispatch } from "../../../../hooks/redux";
import {
  deletePipelineNode,
  setPipelineNodeEdgesType,
  setPipelineNodeParamsOpen,
} from "../../../../redux/sandbox/sandboxSlice";
import { cl } from "../../../../utils/classnames";

const SandboxPipelineMenu: FC<{
  pos: Record<"x" | "y", number> | null;
  onClose(): void;
}> = ({ pos, onClose }) => {
  const dispatch = useAppDispatch();

  const handleEdgesEdit = useCallback(() => {
    dispatch(setPipelineNodeEdgesType("edit"));

    onClose();
  }, [dispatch, onClose]);

  const handleNodeParamsEdit = useCallback(() => {
    dispatch(setPipelineNodeParamsOpen(true));

    onClose();
  }, [dispatch, onClose]);

  const handleNodeDelete = useCallback(() => {
    dispatch(deletePipelineNode());

    onClose();
  }, [onClose, dispatch]);

  const buttons = useMemo<
    { name: string; action(): void; disabled?: boolean }[]
  >(
    () => [
      { name: "edit edges", action: handleEdgesEdit },
      { name: "edit params", action: handleNodeParamsEdit },
      { name: "delete", action: handleNodeDelete },
    ],
    [handleEdgesEdit, handleNodeDelete, handleNodeParamsEdit]
  );

  return (
    <ClickAwayListener onClickAway={onClose}>
      <Paper
        style={{ top: `${pos?.y || 0}px`, left: `${pos?.x || 0}px` }}
        className={cl(scss.root, pos && scss.visible)}
        elevation={3}
      >
        <p className={scss.title}>point menu</p>
        <div className={scss.menu}>
          {buttons.map((item) => (
            <Button
              key={item.name}
              onClick={item.action}
              className={scss.item}
              disabled={item.disabled}
            >
              {item.name}
            </Button>
          ))}
        </div>
      </Paper>
    </ClickAwayListener>
  );
};

export default memo(SandboxPipelineMenu);

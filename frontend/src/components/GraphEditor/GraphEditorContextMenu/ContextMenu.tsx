import React, { FC } from "react";
import style from "./contextMenu.module.scss";
import { dataContextType } from "../GraphEditorDirectedGraph/GraphEditorDirectedGraph";

export interface IContextMenu {
  dataContext: dataContextType | undefined;
  addNode(): void;
  deleteNode(): void;
}

const ContextMenu: FC<IContextMenu> = (props) => {
  let position: any;

  if (props.dataContext) {
    position = {
      position: "absolute",
      top: `${props.dataContext.offset.y}px`,
      left: `${props.dataContext.offset.x}px`,
    };
  }

  return (
    <div className={style.root} style={position}>
      <button onClick={props.addNode}>add node</button>
      <button onClick={props.deleteNode}>edit node</button>
    </div>
  );
};
export default ContextMenu;

import scss from "./showcaseCasesCard.module.scss";

import { FC, memo, useCallback } from "react";

import Button from "@mui/material/Button";
import { useDispatch } from "react-redux";

import { staticAPI } from "../../../../API/baseURL";
import { ICaseItem } from "../../../../API/showcase/showcaseInterface";
import { setSelectedShowcase } from "../../../../redux/showCase/showcaseSlice";

const ShowcaseCasesCard: FC<{ showcase: ICaseItem }> = ({ showcase }) => {
  const dispatch = useDispatch();

  const handleExpand = useCallback(() => {
    dispatch(setSelectedShowcase({ caseId: showcase.case_id }));
  }, [showcase.case_id, dispatch]);

  return (
    <article className={scss.root}>
      <img
        src={staticAPI.getImage(showcase.icon_path)}
        alt={showcase.title}
        className={scss.image}
      />
      <div className={scss.caption}>
        <h3 className={scss.title}>{showcase.title}</h3>
        <Button className={scss.button} onClick={handleExpand}>
          Expand
        </Button>
      </div>
    </article>
  );
};

export default memo(ShowcaseCasesCard);

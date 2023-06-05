import scss from "./historyModal.module.scss";

import { FC, useCallback } from "react";

import CloseIcon from "@mui/icons-material/Close";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import IconButton from "@mui/material/IconButton";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";

import { staticAPI } from "../../../API/baseURL";
import { IHistoryNodeIndividual } from "../../../API/composer/composerInterface";
import { pipelineAPI } from "../../../API/pipeline/pipelineAPI";
import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import { setPipelineUid } from "../../../redux/sandbox/sandboxSlice";
import { cl } from "../../../utils/classnames";

const HistoryModal: FC<{
  node: IHistoryNodeIndividual | null;
  onClose: () => void;
}> = ({ node, onClose }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleEditPipeline = useCallback(() => {
    dispatch(setPipelineUid(node?.individual_id));
    navigate("..");
  }, [dispatch, navigate, node?.individual_id]);

  const { isFetching, data } = pipelineAPI.useGetPipelineImageQuery(
    {
      uid: node?.individual_id,
    },
    { skip: !node }
  );

  return (
    <Dialog open={!!node} onClose={onClose}>
      <div className={scss.header}>
        <p className={scss.title}>{node?.uid}</p>
        <IconButton onClick={onClose} className={"scss.closeButton"}>
          <CloseIcon />
        </IconButton>
      </div>

      <div className={scss.content}>
        {isFetching ? (
          <AppLoader />
        ) : data ? (
          <img
            className={scss.image}
            src={staticAPI.getImage(data.image_url)}
            alt={data.uid}
          />
        ) : (
          <p className={scss.empty}>no data</p>
        )}
      </div>
      <div className={scss.bottom}>
        <Button className={cl(scss.button, scss.cancel)} onClick={onClose}>
          cancel
        </Button>
        <Button
          className={cl(scss.button, scss.submit)}
          onClick={handleEditPipeline}
          disabled={!data || isFetching}
        >
          edit
        </Button>
      </div>
    </Dialog>
  );
};

export default HistoryModal;

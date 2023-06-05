import scss from "./sandboxEpoch.module.scss";

import { useCallback, useEffect, useState } from "react";

import TimelineIcon from "@mui/icons-material/Timeline";

import { sandboxAPI } from "../../../API/sanbox/sandboxAPI";
import { IEpoch } from "../../../API/sanbox/sandboxInterface";
import Slider from "../../../components/UI/Slider/Slider";
import LinearLoader from "../../../components/UI/loaders/linear/LinearLoader";
import { useAppDispatch } from "../../../hooks/redux";
import { useAppParams } from "../../../hooks/useAppParams";
import { setPipelineUid } from "../../../redux/sandbox/sandboxSlice";

const SandboxEpoch = () => {
  const dispatch = useAppDispatch();

  const { caseId } = useAppParams();
  const { data: epoch, isFetching } = sandboxAPI.useGetSandboxEpochQuery(
    { caseId: caseId || "" },
    { skip: !caseId }
  );

  const [selected, setSelected] = useState<IEpoch | null>(null);

  const handleChange = useCallback(
    (event: unknown, value: number | number[]) => {
      setSelected(epoch && typeof value === "number" ? epoch[value - 1] : null);
    },
    [epoch]
  );

  useEffect(() => {
    selected && dispatch(setPipelineUid(selected.individual_id));
  }, [selected, dispatch]);

  return (
    <section className={scss.root}>
      <TimelineIcon className={scss.icon} />
      <h2 className={scss.title}>Epoch</h2>
      <div className={scss.content}>
        {isFetching ? (
          <LinearLoader />
        ) : (
          epoch && (
            <Slider
              defaultValue={epoch.length}
              onChange={handleChange}
              onChangeCommitted={handleChange}
              min={1}
              max={epoch.length}
              marks
              valueLabelDisplay="auto"
            />
          )
        )}
      </div>
    </section>
  );
};

export default SandboxEpoch;

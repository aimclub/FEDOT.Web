import scss from "./sandboxPage.module.scss";

import { useEffect } from "react";

import { showcaseAPI } from "../../API/showcase/showcaseAPI";
import { useAppDispatch, useAppSelector } from "../../hooks/redux";
import { useAppParams } from "../../hooks/useAppParams";
import { setPipelineUid } from "../../redux/sandbox/sandboxSlice";
import SandboxCharts from "./charts/SandboxCharts";
import SandboxEpoch from "./epoch/SandboxEpoch";
import SandboxPipeline from "./pipeline/SandboxPipeline";

const SandboxPage = () => {
  const { caseId } = useAppParams();
  const { pipeline_uid } = useAppSelector((state) => state.sandbox);
  const { data: showcase } = showcaseAPI.useGetShowcaseQuery(
    { caseId: caseId || "" },
    { skip: !!pipeline_uid || !caseId }
  );

  const dispatch = useAppDispatch();

  useEffect(() => {
    return () => {
      dispatch(setPipelineUid(""));
    };
  }, [dispatch]);

  useEffect(() => {
    showcase && dispatch(setPipelineUid(showcase.individual_id));
  }, [dispatch, showcase]);

  return (
    <div className={scss.root}>
      <SandboxPipeline />
      <SandboxEpoch />
      <SandboxCharts />
    </div>
  );
};

export default SandboxPage;

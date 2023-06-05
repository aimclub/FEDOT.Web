import { useCallback, useEffect } from "react";
import { pipelineAPI } from "../../../API/pipeline/pipelineAPI";

import scss from "./sandboxPipeline.module.scss";

import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import { useAppDispatch, useAppSelector } from "../../../hooks/redux";
import {
  setPipeline,
  setPipelineUid,
} from "../../../redux/sandbox/sandboxSlice";
import SandboxPipelineButtons from "./buttons/SandboxPipelineButtons";
import SandboxPipelineGraph from "./graph/SandboxPipelineGraph";
import SandboxPipelineNodeEdges from "./nodeEdges/SandboxPipelineNodeEdges";
import SandboxPipelineNodeParams from "./nodeParams/SandboxPipelineNodeParams";

const SandboxPipeline = () => {
  const dispatch = useAppDispatch();
  const { pipeline_uid, pipeline } = useAppSelector((state) => state.sandbox);

  const { isFetching, data } = pipelineAPI.useGetPipelineQuery(
    { uid: pipeline_uid },
    { skip: !pipeline_uid }
  );

  const [validatePipeline, { isLoading: isValidate }] =
    pipelineAPI.useValidatePipelineMutation();
  const [addPipeline, { isLoading: isAdding, data: addData }] =
    pipelineAPI.useAddPipelineMutation();

  const handleEvaluatePipeline = useCallback(() => {
    if (!pipeline) return;
    validatePipeline(pipeline).then((res) => {
      const checkIsError = (res: unknown): res is { error: unknown } =>
        !!res && !!(res as { error: unknown }).error;

      if (!checkIsError(res)) {
        alert("Graph is valid. Added.");
        addPipeline(pipeline);
      } else {
        alert(res.error);
      }
    });
  }, [addPipeline, pipeline, validatePipeline]);

  useEffect(() => {
    dispatch(setPipeline(data));
  }, [dispatch, data]);

  useEffect(() => {
    if (addData) {
      dispatch(setPipelineUid(addData?.uid));
    }
  }, [dispatch, addData]);

  return (
    <section className={scss.root}>
      <div className={scss.graph}>
        <SandboxPipelineGraph />
      </div>
      <SandboxPipelineButtons
        disabled={!data || isFetching || isValidate || isAdding}
        onEvaluate={handleEvaluatePipeline}
      />
      <SandboxPipelineNodeEdges />
      <SandboxPipelineNodeParams />
      {(isFetching || isValidate || isAdding) && (
        <AppLoader hasBlackout={true} />
      )}
    </section>
  );
};

export default SandboxPipeline;

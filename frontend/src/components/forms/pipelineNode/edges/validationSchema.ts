import * as Yup from "yup";
import { IPipelineNodesEdgesValues } from "./PipelineNodeEdgesForm";
import {
  VALIDATION_MESSAGES,
  ValidationSchemaShapeType,
} from "../../../../utils/validation";

export const validationSchema = Yup.object().shape<
  ValidationSchemaShapeType<IPipelineNodesEdgesValues>
>({
  display_name: Yup.string().required(VALIDATION_MESSAGES.required),
});

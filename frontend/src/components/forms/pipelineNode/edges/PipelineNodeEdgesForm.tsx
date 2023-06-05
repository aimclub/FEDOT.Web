import scss from "./pipelineNodeEdgesForm.module.scss";

import { FC, memo, useEffect, useMemo } from "react";

import Button from "@mui/material/Button";
import { useFormik } from "formik";

import { NodeDataType } from "../../../../API/pipeline/pipelineInterface";
import { useAppSelector } from "../../../../hooks/redux";
import { useGetNodeDisplayNames } from "../../../../hooks/useGetNodeDisplayNames";
import { cl } from "../../../../utils/classnames";
import AppSelect from "../../../UI/selects/AppSelect";
import AppSelectMulti from "../../../UI/selects/AppSelectMulti";
import TextFieldUnderline from "../../../UI/textfields/TextFieldUnderline";
import { validationSchema } from "./validationSchema";

export interface IPipelineNodesEdgesValues {
  id?: number;
  display_name: string;
  children: number[];
  parents: number[];
  type: NodeDataType | "";
}

const INITIAL_VALUES: IPipelineNodesEdgesValues = {
  display_name: "",
  children: [],
  parents: [],
  type: "",
};

const PipelineNodeEdgesForm: FC<{
  initialValues: IPipelineNodesEdgesValues | null;
  onSubmit(values: IPipelineNodesEdgesValues): void;
  onClose(): void;
}> = ({ initialValues, onSubmit, onClose }) => {
  const { pipeline } = useAppSelector((state) => state.sandbox);

  const {
    values,
    errors,
    touched,
    handleChange,
    handleSubmit,
    resetForm,
    setFieldValue,
  } = useFormik<IPipelineNodesEdgesValues>({
    initialValues: initialValues || INITIAL_VALUES,
    validationSchema,
    onSubmit,
  });

  const { displayNames, modelNames } = useGetNodeDisplayNames(
    initialValues?.display_name
  );

  const avaliableNodes = useMemo(
    () =>
      pipeline?.nodes
        .filter((i) => i.id !== values.id)
        .map((n) => ({ id: n.id, name: `${n.id}` })) || [],
    [pipeline?.nodes, values.id]
  );

  useEffect(() => {
    resetForm({ values: initialValues || INITIAL_VALUES });
  }, [initialValues, resetForm]);

  useEffect(() => {
    setFieldValue(
      "type",
      modelNames?.find((i) => i.display_name === values.display_name)?.type
    );
  }, [modelNames, setFieldValue, values.display_name]);

  return (
    <form onSubmit={handleSubmit} className={scss.root}>
      <div className={scss.item}>
        <p
          className={cl(
            scss.text,
            touched.display_name && errors.display_name && scss.error
          )}
        >
          Display_name:
        </p>
        <AppSelect
          value={values.display_name}
          onChange={handleChange}
          name="display_name"
          availableValues={displayNames}
          error={touched.display_name && !!errors.display_name}
        />
      </div>

      <div className={scss.item}>
        <p className={scss.text}>Parents ids: </p>
        <AppSelectMulti
          availableValues={avaliableNodes}
          value={values.parents}
          onChange={handleChange}
          name="parents"
        />
      </div>

      <div className={scss.item}>
        <p className={scss.text}>Childrens ids: </p>
        <AppSelectMulti
          availableValues={avaliableNodes}
          value={values.children}
          onChange={handleChange}
          name="children"
        />
      </div>

      <div className={scss.item}>
        <p className={scss.text}>Type: </p>
        <TextFieldUnderline name="type" value={values.type || ""} disabled />
      </div>

      <div className={scss.bottom}>
        <Button className={cl(scss.button, scss.cancel)} onClick={onClose}>
          cancel
        </Button>
        <Button type="submit" className={cl(scss.button, scss.submit)}>
          apply
        </Button>
      </div>
    </form>
  );
};

export default memo(PipelineNodeEdgesForm);

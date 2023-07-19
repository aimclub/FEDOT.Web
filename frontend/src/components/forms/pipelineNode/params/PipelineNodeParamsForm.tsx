import scss from "./pipelineNodeParamsForm.module.scss";

import { FC, memo, useCallback, useEffect } from "react";

import StarRateIcon from "@mui/icons-material/StarRate";
import Button from "@mui/material/Button";
import { useFormik } from "formik";
import AddIcon from "@mui/icons-material/Add";

import { INodeData } from "../../../../API/pipeline/pipelineInterface";
import { useGetNodeDisplayNames } from "../../../../hooks/useGetNodeDisplayNames";
import { cl } from "../../../../utils/classnames";
import AppSelect from "../../../UI/selects/AppSelect";
import TextFieldUnderline from "../../../UI/textfields/TextFieldUnderline";
import PipelineNodeParamsFormItem from "./item/PipelineNodeParamsFormItem";

const INITIAL_VALUES: INodeData = {
  children: [],
  display_name: "",
  id: 0,
  model_name: "",
  params: "default_params",
  parents: [],
  type: "model",
};

const PipelineNodeParamsForm: FC<{
  initialValues: INodeData | null;
  onSubmit(values: INodeData): void;
  onClose(): void;
}> = ({ initialValues, onSubmit, onClose }) => {
  const {
    values,
    errors,
    touched,
    handleChange,
    handleSubmit,
    resetForm,
    setFieldValue,
  } = useFormik<{ node: INodeData; newParam: string }>({
    initialValues: { node: initialValues || INITIAL_VALUES, newParam: "" },
    onSubmit: () => {
      //
    },
  });

  const { displayNames } = useGetNodeDisplayNames(initialValues?.display_name);

  const handleDeleteParam = useCallback(
    (key: string) => {
      setFieldValue(`node.params.${key}`, undefined);
    },
    [setFieldValue]
  );

  const handleAddParam = useCallback(() => {
    const newParam = values.newParam.trim();
    if (typeof values.node.params === "object") {
      setFieldValue(`node.params.${newParam}`, "");
    } else {
      setFieldValue(`node.params`, { [newParam]: "" });
    }
    setFieldValue("newParam", "");
  }, [setFieldValue, values.newParam, values.node.params]);

  const handleSubmitForm = useCallback(() => {
    onSubmit(values.node);
  }, [onSubmit, values.node]);

  useEffect(() => {
    resetForm({
      values: { node: initialValues || INITIAL_VALUES, newParam: "" },
    });
  }, [initialValues, resetForm]);

  return (
    <form className={scss.root} onSubmit={handleSubmit}>
      <div className={scss.top}>
        <div className={scss.ratting}>
          <StarRateIcon className={scss.icon} />
          <p className={scss.text}>{`Rating ${
            values.node.rating || "?"
          }/10`}</p>
        </div>
        <p className={scss.text}>{`id: ${values.node.id}`}</p>
      </div>

      <div className={scss.field}>
        <p
          className={cl(
            scss.text,
            touched.node?.display_name &&
              errors.node?.display_name &&
              scss.error
          )}
        >
          Display_name:
        </p>
        <AppSelect
          value={values.node.display_name}
          onChange={handleChange}
          name="display_name"
          availableValues={displayNames}
          error={touched.node?.display_name && !!errors.node?.display_name}
        />
      </div>

      <div>
        <p className={scss.text}>Hyperparameters:</p>
        <div className={scss.params}>
          {typeof values.node.params === "object" ? (
            <>
              <div className={cl(scss.row, scss.head)}>
                {[String.fromCharCode(8470), "NameParam", "value"].map(
                  (item) => (
                    <span key={item}>{item}</span>
                  )
                )}
              </div>
              {Object.entries(values.node.params).map(([key, value], index) => (
                <PipelineNodeParamsFormItem
                  key={key}
                  className={scss.row}
                  index={index + 1}
                  value={value}
                  onChange={handleChange}
                  name={key}
                  onDeleteParam={handleDeleteParam}
                />
              ))}
            </>
          ) : (
            <p className={scss.null}>{`${values.node.params}`}</p>
          )}
        </div>

        <div className={scss.add}>
          <p className={"classes.addParamLabel"}>NameParam</p>
          <TextFieldUnderline
            name="newParam"
            value={values.newParam}
            onChange={handleChange}
            onKeyDown={(e) => e.key === "Enter" && handleAddParam()}
            // className={classes.addParamInput}
          />
          <Button
            onClick={handleAddParam}
            className={scss.button}
            disabled={values.newParam.trim() === ""}
          >
            <AddIcon className={scss.icon} />
            <span>add</span>
          </Button>
        </div>
      </div>

      <div className={scss.bottom}>
        <Button className={cl(scss.button, scss.cancel)} onClick={onClose}>
          cancel
        </Button>
        <Button
          className={cl(scss.button, scss.submit)}
          onClick={handleSubmitForm}
        >
          apply
        </Button>
      </div>
    </form>
  );
};
export default memo(PipelineNodeParamsForm);

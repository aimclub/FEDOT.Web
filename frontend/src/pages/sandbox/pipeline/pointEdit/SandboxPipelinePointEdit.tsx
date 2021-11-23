import React, { FC, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Button, Fade, IconButton, Paper } from "@material-ui/core";
import CloseIcon from "@material-ui/icons/Close";

import { useStyles } from "./SandboxPipelinePointEditStyle";

import AppSelect from "../../../../components/UI/selects/AppSelect";
import { actionsPipeline } from "../../../../redux/pipeline/pipeline-actions";
import { StateType } from "../../../../redux/store";
import { SandboxPointFormType } from "../../../../redux/pipeline/pipeline-types";
import { useFormik } from "formik";
import TextFieldUnderline from "../../../../components/UI/textfields/TextFieldUnderline";
import CustomTooltip from "../../../../components/UI/tooltip/CustomTooltip";
import AppSelectMulti from "../../../../components/UI/selects/AppSelectMulti";
import { NodeDataType } from "../../../../API/pipeline/pipelineInterface";
import { validationSchema } from "./validationPointEdit";

const creatingConnections = (
  id: number,
  childrens: number[],
  parents: number[]
) => {
  let childrensArr: { source: number; target: number }[] = [];
  let paretnsArr: { source: number; target: number }[] = [];

  if (childrens.length !== 0) {
    childrensArr = childrens.map((item) => {
      return { source: id, target: item };
    });
  }
  if (parents.length !== 0) {
    paretnsArr = parents.map((item) => {
      return { source: item, target: id };
    });
  }

  return [...childrensArr, ...paretnsArr];
};

const SandboxPipelinePointEdit: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { isOpen, node, type } = useSelector(
    (state: StateType) => state.pipeline.pointEdit
  );
  const { pipeline } = useSelector((state: StateType) => state.pipeline);
  const { modelNames } = useSelector((state: StateType) => state.sandbox);
  const [nodeType, setNodeType] = useState<NodeDataType>(node?.type || "model");

  const initialValues = {
    displayName: node?.display_name || "",
    children:
      node?.children?.filter((n) => pipeline?.nodes?.some((i) => i.id === n)) ||
      [],
    parents:
      node?.parents?.filter((n) => pipeline?.nodes?.some((i) => i.id === n)) ||
      [],
  };

  const formik = useFormik({
    initialValues,
    validationSchema,
    onSubmit: (values) => {
      const id = node
        ? node.id
        : Math.max(...pipeline.nodes.map((i) => i.id), 0) + 1;
      const newEdges = creatingConnections(id, values.children, values.parents);
      if (type === SandboxPointFormType.EDIT) {
        dispatch(
          actionsPipeline.editPipelineNode(
            pipeline,
            {
              ...node,
              id,
              display_name: values.displayName,
              model_name: values.displayName,
              type: nodeType,
              parents: values.parents,
              children: values.children,
            },
            newEdges
          )
        );
      } else {
        dispatch(
          actionsPipeline.addPipelineNode({
            node: {
              id,
              display_name: values.displayName,
              model_name: values.displayName,
              type: nodeType,
              params: {},
              parents: values.parents,
              children: values.children,
            },
            edges: newEdges,
          })
        );

        dispatch(actionsPipeline.closePointEdit());
      }
    },
  });

  const handleClose = () => {
    dispatch(actionsPipeline.closePointEdit());
  };

  useEffect(() => {
    formik.resetForm({ values: initialValues });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node]);

  useEffect(() => {
    setNodeType(
      modelNames.find((i) => i.display_name === formik.values.displayName)
        ?.type || "model"
    );
  }, [formik.values.displayName, modelNames]);

  return (
    <Fade in={isOpen} mountOnEnter unmountOnExit>
      <Paper elevation={3} className={classes.dialog}>
        <div className={classes.header}>
          <p className={classes.title}>
            {type === SandboxPointFormType.ADD_NEW
              ? "add Point"
              : `edit Point id:${node?.id}`}
          </p>
          <IconButton className={classes.closeButton} onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </div>
        <form className={classes.content} onSubmit={formik.handleSubmit}>
          <div className={classes.contentLine}>
            <CustomTooltip
              placement="top"
              arrow
              title={formik.values.displayName}
            >
              <p
                className={`${classes.text} ${
                  !!formik.errors.displayName && classes.error
                }`}
              >
                Display_name:{" "}
              </p>
            </CustomTooltip>
            <AppSelect
              classname={classes.value}
              name="displayName"
              currentValue={formik.values.displayName}
              availableValues={modelNames.map((n) => ({
                id: n.display_name,
                name: n.display_name,
              }))}
              onChange={formik.handleChange}
              disabled={type === SandboxPointFormType.EDIT}
              error={formik.errors.displayName}
            />
          </div>

          <div className={classes.contentLine}>
            <p className={classes.text}>Parents ids: </p>
            <AppSelectMulti
              classname={classes.value}
              name="parents"
              currentValue={formik.values.parents}
              availableValues={
                pipeline?.nodes
                  ? pipeline?.nodes
                      .filter((n) => n.id !== node?.id)
                      .map((n) => ({ id: n.id, name: `${n.id}` }))
                  : []
              }
              onChange={formik.handleChange}
            />
          </div>

          <div className={classes.contentLine}>
            <p className={classes.text}>Childrens ids: </p>
            <AppSelectMulti
              classname={classes.value}
              name="children"
              currentValue={formik.values.children}
              availableValues={
                pipeline?.nodes
                  ? pipeline?.nodes
                      .filter((n) => n.id !== node?.id)
                      .map((n) => ({ id: n.id, name: `${n.id}` }))
                  : []
              }
              onChange={formik.handleChange}
            />
          </div>

          <div className={classes.contentLine}>
            <p className={classes.text}>Type: </p>
            <TextFieldUnderline name="type" value={nodeType} disabled={true} />
          </div>

          <div className={classes.buttonGroup}>
            <Button
              className={`${classes.button} ${classes.cancelButton}`}
              onClick={handleClose}
            >
              cancel
            </Button>
            <Button
              type="submit"
              className={`${classes.button} ${classes.submitButton}`}
            >
              apply
            </Button>
          </div>
        </form>
      </Paper>
    </Fade>
  );
};

export default SandboxPipelinePointEdit;

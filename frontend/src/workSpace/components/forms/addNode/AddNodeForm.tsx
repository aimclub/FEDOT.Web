import React, { FC, memo } from "react";
import { useFormik } from "formik";
import { useDispatch, useSelector } from "react-redux";
import scss from "./addNodeForm.module.scss";

import { makeStyles, createStyles } from "@material-ui/core/styles";
import { Paper } from "@material-ui/core";

import AddNodeFormTitle from "./AddNodeFormTitle";
import AddNodeFormName from "./name/AddNodeFormName";
import { StateType } from "../../../../redux/store";
import AddNodeFormParents from "./parents/AddNodeFormParents";
import AddNodeFormChildren from "./children/AddNodeFormChildren";
import AddNodeFormType from "./type/AddNodeFormType";
import { actionsSandbox } from "../../../../redux/reducers/sandBox/sandbox-reducer";
import ButtonsCancelAndSubmit from "../../../../ui/formik/buttons/ButtonsCancelAndSubmit";

const useStyles = makeStyles(() =>
  createStyles({
    root: {
      width: 278,

      position: "absolute",
      right: 0,

      zIndex: 3,
    },
    buttonsPosition: {
      marginTop: 16,
    },
  })
);

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

interface I {
  setFromClosed(): void;
}

const AddNodeForm: FC<I> = ({ setFromClosed }) => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { mainGraph } = useSelector((state: StateType) => state.sandbox_Egor);

  const formik = useFormik({
    initialValues: {
      name: "",
      id: mainGraph.nodes.length,
      parents: "",
      children: "",
      type: "model", //должен быть select
    },
    // validationSchema,
    onSubmit: (values) => {
      // console.log(`values`, values);
      // создаем массив стрелок
      creatingConnections(
        values.id,
        JSON.parse(`[${values.children}]`),
        JSON.parse(`[${values.parents}]`)
      );

      dispatch(
        actionsSandbox.addNodeMainGraph({
          nodes: [
            {
              id: values.id,
              display_name: values.name,
              model_name: values.name,
              type: values.type,
              params: {},
              parents: JSON.parse(`[${values.parents}]`),
              children: JSON.parse(`[${values.children}]`),
            },
          ],
          edges: creatingConnections(
            values.id,
            JSON.parse(`[${values.children}]`),
            JSON.parse(`[${values.parents}]`)
          ),
        })
      );
      setFromClosed();
    },
  });

  return (
    <Paper elevation={3} className={classes.root}>
      <AddNodeFormTitle title="add Point" />
      <div className={scss.formRoot}>
        <form onSubmit={formik.handleSubmit}>
          <AddNodeFormName
            values={formik.values}
            onChange={formik.handleChange}
          />
          <AddNodeFormParents
            values={formik.values}
            onChange={formik.handleChange}
          />
          <AddNodeFormChildren
            values={formik.values}
            onChange={formik.handleChange}
          />
          <AddNodeFormType
            values={formik.values}
            onChange={formik.handleChange}
          />
          <div className={classes.buttonsPosition}>
            <ButtonsCancelAndSubmit
              disabled={false}
              onCancelClick={setFromClosed}
            />
          </div>
        </form>
      </div>
    </Paper>
  );
};

export default memo(AddNodeForm);

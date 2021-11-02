import React, { FC, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { Button, Grid, IconButton } from "@material-ui/core";
import AddIcon from "@material-ui/icons/Add";
import CloseIcon from "@material-ui/icons/Close";

import { useStyles } from "./SandboxPipelineNodeEditParamsStyle";

import TextFieldUnderline from "../../../../../components/UI/textfields/TextFieldUnderline";
import CustomTooltip from "../../../../../components/UI/tooltip/CustomTooltip";
import { actionsPipeline } from "../../../../../redux/pipeline/pipeline-actions";
import { StateType } from "../../../../../redux/store";

const SandboxPipelineNodeEditParams: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { node } = useSelector((state: StateType) => state.pipeline.nodeEdit);
  const [addParamName, setAddParamName] = useState<string>("");

  const handleParamNameChange = (event: any) => {
    const { value } = event.target;
    setAddParamName(value);
  };

  const handleParamAdd = (event: any) => {
    event.preventDefault();
    const newParamName = addParamName.replace(/\s/g, "");
    dispatch(
      actionsPipeline.setNodeEditData({
        ...node,
        params:
          typeof node.params === "object"
            ? { ...node.params, [newParamName]: "" }
            : { [newParamName]: "" },
      })
    );
  };

  const handeleParamDelete = (paramName: string) => {
    const newParams = node.params as {
      [key: string]: string | boolean | number;
    };
    delete newParams[paramName];
    dispatch(
      actionsPipeline.setNodeEditData({
        ...node,
        params:
          Object.keys(newParams).length > 0 ? newParams : "default_params",
      })
    );
  };

  const handleParamValueChange = (event: any) => {
    const { value, name } = event.target;
    dispatch(
      actionsPipeline.setNodeEditData({
        ...node,
        params: { ...(node.params as object), [name]: value },
      })
    );
  };

  return (
    <div>
      <p className={classes.title}>Hyperparameters:</p>
      <div className={classes.content}>
        {typeof node.params === "object" ? (
          <>
            <Grid container className={classes.header}>
              <Grid item xs={1}>
                &#8470;
              </Grid>
              <Grid item xs={5}>
                NameParam
              </Grid>
              <Grid item xs={6}>
                value
              </Grid>
            </Grid>
            {Object.entries(node.params).map(([key, value], i) => (
              <Grid container key={key} className={classes.paramLine}>
                <Grid item xs={1}>
                  {i + 1}
                </Grid>
                <Grid item xs={5}>
                  <CustomTooltip
                    title={`${key}: ${value}`}
                    placement="top"
                    arrow
                  >
                    <p className={classes.paramName}>{key}</p>
                  </CustomTooltip>
                </Grid>
                <Grid item xs={5}>
                  <TextFieldUnderline
                    name={key}
                    value={(node.params as { [key: string]: any })[key]}
                    onChange={handleParamValueChange}
                  />
                </Grid>
                <Grid item xs={1}>
                  <IconButton
                    className={classes.deleteParam}
                    onClick={() => {
                      handeleParamDelete(key);
                    }}
                  >
                    <CloseIcon className={classes.deleteParamIcon} />
                  </IconButton>
                </Grid>
              </Grid>
            ))}
          </>
        ) : (
          <p className={classes.empty}>{`${node.params}`}</p>
        )}
      </div>
      <form className={classes.addParamForm} onSubmit={handleParamAdd}>
        <p className={classes.addParamLabel}>NameParam</p>
        <TextFieldUnderline
          name="paramName"
          value={addParamName}
          onChange={handleParamNameChange}
          className={classes.addParamInput}
        />
        <Button
          className={classes.buttonAdd}
          type="submit"
          disabled={addParamName.trim() === ""}
        >
          <AddIcon className={classes.buttonIcon} />
          <span className={classes.buttonText}>add</span>
        </Button>
      </form>
    </div>
  );
};

export default SandboxPipelineNodeEditParams;

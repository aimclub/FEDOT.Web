import { useFormik } from "formik";
import React, { FC, memo, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { makeStyles } from "@material-ui/core/styles";

import { actionsAuth } from "../../../redux/auth/auth-action";
import { StateType } from "../../../redux/store";
import SignInButonSubmit from "../../UI/buttons/SignInButonSubmit";
import TextFieldFormikSignIn from "../../UI/textfields/TextFieldFormikSignIn";
import { validationSchema } from "./validationSiginUp";

const useStyles = makeStyles(() => ({
  root: {
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    justifyContent: "center",
  },
  error: {
    padding: 10,
    minHeight: 50,
    boxSizing: "border-box",

    fontFamily: "'Open Sans'",
    fontStyle: "normal",
    fontWeight: 400,
    fontSize: 14,
    lineHeight: "120%",
    color: "#D32F2F",

    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    justifyContent: "flex-end",
  },
}));

const SignUpForm: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { authError } = useSelector((state: StateType) => state.auth);

  const formik = useFormik({
    initialValues: {
      login: "",
      password: "",
      passwordConfirm: "",
    },
    validationSchema,
    onSubmit: (values) => {
      dispatch(actionsAuth.register(values.login, values.password));
    },
  });

  useEffect(() => {
    dispatch(actionsAuth.setError(null));
  }, [dispatch]);

  return (
    <form onSubmit={formik.handleSubmit} className={classes.root}>
      <TextFieldFormikSignIn
        name="login"
        label="login *"
        value={formik.values.login}
        onChange={formik.handleChange}
        error={formik.touched.login ? formik.errors.login : undefined}
      />
      <TextFieldFormikSignIn
        name="password"
        label="password *"
        type="password"
        value={formik.values.password}
        onChange={formik.handleChange}
        error={formik.touched.password ? formik.errors.password : undefined}
      />
      <TextFieldFormikSignIn
        name="passwordConfirm"
        label="password *"
        type="password"
        value={formik.values.passwordConfirm}
        onChange={formik.handleChange}
        error={
          formik.touched.passwordConfirm
            ? formik.errors.passwordConfirm
            : undefined
        }
      />
      <div className={classes.error}>
        {authError && (
          <>
            <p>Authorization error!</p>
            <p>{`${authError}`}</p>
          </>
        )}
      </div>

      <SignInButonSubmit>
        <span>Register</span>
      </SignInButonSubmit>
    </form>
  );
};

export default memo(SignUpForm);

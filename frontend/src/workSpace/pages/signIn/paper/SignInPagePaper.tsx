import React from "react";
import scss from "./signInPagePaper.module.scss";

import { Paper } from "@material-ui/core";
import SignInForm from "../../../components/forms/signIn/SignInForm";

const SignInPagePaper = () => {
  return (
    <section>
      <Paper elevation={3} className={scss.root}>
        <p className={scss.title}>Sign In</p>
        <SignInForm />
      </Paper>
    </section>
  );
};

export default SignInPagePaper;

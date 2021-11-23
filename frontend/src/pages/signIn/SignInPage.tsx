import React, { FC } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, Redirect, Route, Switch } from "react-router-dom";

import { Button, Paper } from "@material-ui/core";

import { useStyles } from "./SignInPageStyle";

import SignInForm from "../../components/forms/signIn/SignInForm";
import SignUpForm from "../../components/forms/signUp/SignUpForm";
import AppLoader from "../../components/UI/loaders/AppLoader";
import { actionsAuth } from "../../redux/auth/auth-action";
import { StateType } from "../../redux/store";
import { AppRoutesEnum } from "../../routes";

const SignInPage: FC = () => {
  const classes = useStyles();
  const dispatch = useDispatch();
  const { isAuth, isLoading } = useSelector((state: StateType) => state.auth);

  const handleSignInAsGuest = () => {
    dispatch(actionsAuth.singIn("guest", "guest"));
  };

  return isAuth ? (
    <Redirect to={AppRoutesEnum.SHOWCASE} />
  ) : (
    <main className={classes.root}>
      <div className={classes.logo} />
      <Switch>
        <Route exact path={AppRoutesEnum.SIGNIN}>
          <Paper className={classes.paper} component="section" elevation={3}>
            {isLoading && <AppLoader hasBlackout />}
            <h1 className={classes.title}>Sign In</h1>
            <SignInForm />
            <div className={classes.foot}>
              <Link to={AppRoutesEnum.SIGNUP} className={classes.footItem}>
                Not registered yet? Register
              </Link>
              <Button
                onClick={handleSignInAsGuest}
                className={classes.footItem}
              >
                Sign In as guest
              </Button>
            </div>
          </Paper>
        </Route>
        <Route exact path={AppRoutesEnum.SIGNUP}>
          <Paper className={classes.paper} component="section" elevation={3}>
            {isLoading && <AppLoader hasBlackout />}
            <h1 className={classes.title}>Registration</h1>
            <SignUpForm />
            <div className={classes.foot}>
              <Link to={AppRoutesEnum.SIGNIN} className={classes.footItem}>
                Already registered? Sign In
              </Link>
              <Button
                onClick={handleSignInAsGuest}
                className={classes.footItem}
              >
                Sign In as guest
              </Button>
            </div>
          </Paper>
        </Route>
      </Switch>
    </main>
  );
};

export default SignInPage;

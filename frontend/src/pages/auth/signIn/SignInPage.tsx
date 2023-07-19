import scss from "../authPage.module.scss";

import Button from "@mui/material/Button";
import { useCallback } from "react";
import { Link } from "react-router-dom";

import { authAPI } from "../../../API/auth/authAPI";
import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import SignInForm from "../../../components/forms/auth/SignInForm";
import { AppRoutesEnum } from "../../../router/routes";

const SignInPage = () => {
  const [signIn, { isLoading, isError }] = authAPI.useSigninMutation();

  const handleSignInAsGuest = useCallback(() => {
    signIn({ email: "guest", password: "guest" });
  }, [signIn]);

  return (
    <>
      {isLoading && <AppLoader hasBlackout />}
      <h1 className={scss.title}>Sign In</h1>
      <SignInForm signIn={signIn} isError={isError} />
      <div className={scss.foot}>
        <Link to={AppRoutesEnum.SIGNUP} className={scss.footItem}>
          Not registered yet? Register
        </Link>
        <Button onClick={handleSignInAsGuest} className={scss.footItem}>
          Sign In as guest
        </Button>
      </div>
    </>
  );
};

export default SignInPage;

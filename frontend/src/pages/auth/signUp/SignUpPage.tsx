import scss from "../authPage.module.scss";

import Button from "@mui/material/Button";
import { useCallback } from "react";
import { Link } from "react-router-dom";

import { authAPI } from "../../../API/auth/authAPI";
import AppLoader from "../../../components/UI/loaders/app/AppLoader";
import SignUpForm from "../../../components/forms/auth/SignUpForm";
import { AppRoutesEnum } from "../../../router/routes";

const SignUpPage = () => {
  const [signIn, { isLoading: isLoadingAuth, isError: isErrorAuth }] =
    authAPI.useSigninMutation();
  const [register, { isLoading, isError }] = authAPI.useRegisterMutation();

  const handleSignInAsGuest = useCallback(() => {
    signIn({ email: "guest", password: "guest" });
  }, [signIn]);

  return (
    <>
      {(isLoading || isLoadingAuth) && <AppLoader hasBlackout />}
      <h1 className={scss.title}>Registration</h1>
      <SignUpForm signUp={register} isError={isError || isErrorAuth} />
      <div className={scss.foot}>
        <Link to={AppRoutesEnum.SIGNIN} className={scss.footItem}>
          Already registered? Sign In
        </Link>
        <Button onClick={handleSignInAsGuest} className={scss.footItem}>
          Sign In as guest
        </Button>
      </div>
    </>
  );
};

export default SignUpPage;

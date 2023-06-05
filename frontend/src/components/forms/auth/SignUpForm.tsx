import scss from "./auth.module.scss";

import { FC, memo } from "react";

import { IAuth } from "../../../API/auth/authInterface";
import { useFormik } from "formik";
import TextFieldFormikSignIn from "../../UI/textfields/TextFieldFormikSignIn";
import SignInButonSubmit from "../../UI/buttons/SignInButonSubmit";
import { validationSchemaTwoPassword } from "./validationSchema";

export interface ISignUp extends IAuth {
  confirm_password: string;
}

const SignUpForm: FC<{
  signUp: (values: IAuth) => void;
  isError?: boolean;
}> = ({ signUp, isError }) => {
  const { handleSubmit, handleChange, values, errors, touched } =
    useFormik<ISignUp>({
      initialValues: {
        email: "",
        password: "",
        confirm_password: "",
      },
      validationSchema: validationSchemaTwoPassword,
      onSubmit: (values) =>
        signUp({ email: values.email, password: values.password }),
    });

  return (
    <form onSubmit={handleSubmit} className={scss.root}>
      <TextFieldFormikSignIn
        name="email"
        label="login *"
        value={values.email}
        onChange={handleChange}
        error={touched.email ? errors.email : undefined}
      />
      <TextFieldFormikSignIn
        name="password"
        label="password *"
        type="password"
        value={values.password}
        onChange={handleChange}
        error={touched.password ? errors.password : undefined}
      />

      <TextFieldFormikSignIn
        name="confirm_password"
        label="password *"
        type="password"
        value={values.confirm_password}
        onChange={handleChange}
        error={touched.confirm_password ? errors.confirm_password : undefined}
      />

      <div className={scss.error}>{isError && <p>Authorization error!</p>}</div>

      <SignInButonSubmit type="submit">
        <span>Register</span>
      </SignInButonSubmit>
    </form>
  );
};

export default memo(SignUpForm);

import scss from "./auth.module.scss";

import { useFormik } from "formik";
import { FC, memo } from "react";

import { IAuth } from "../../../API/auth/authInterface";
import SignInButonSubmit from "../../UI/buttons/SignInButonSubmit";
import TextFieldFormikSignIn from "../../UI/textfields/TextFieldFormikSignIn";
import { validationSchema } from "./validationSchema";

const SignInForm: FC<{
  signIn: (values: IAuth) => void;
  isError?: boolean;
}> = ({ signIn, isError }) => {
  const { handleSubmit, handleChange, values, errors, touched } =
    useFormik<IAuth>({
      initialValues: {
        email: "",
        password: "",
      },
      validationSchema,
      onSubmit: signIn,
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

      <div className={scss.error}>{isError && <p>Authorization error!</p>}</div>

      <SignInButonSubmit type="submit">
        <span>Sign In</span>
      </SignInButonSubmit>
    </form>
  );
};

export default memo(SignInForm);

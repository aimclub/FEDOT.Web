import * as Yup from "yup";

export const validationSchema = Yup.object({
  login: Yup.string()
    .min(2, "Mininum 2 characters")
    .max(15, "Maximum 15 characters")
    .required("Required!"),
  password: Yup.string()
    //   .min(8, "Minimum 8 characters")
    .required("Required!"),
  // confirm_password: Yup.string()
  //   .oneOf([Yup.ref("password")], "Password's not match")
  //   .required("Required!")
});

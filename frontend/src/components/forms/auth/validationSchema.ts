import * as Yup from "yup";
import { IAuth } from "../../../API/auth/authInterface";
import {
  VALIDATION_MESSAGES,
  ValidationSchemaShapeType,
} from "../../../utils/validation";
import { ISignUp } from "./SignUpForm";

const email = Yup.string()
  .min(2, ({ min }) => VALIDATION_MESSAGES.min(min))
  .max(15, ({ max }) => VALIDATION_MESSAGES.max(max))
  .required(VALIDATION_MESSAGES.required);

const password = Yup.string()
  //   .min(8, "Minimum 8 characters")
  .required(VALIDATION_MESSAGES.required);

export const validationSchema = Yup.object().shape<
  ValidationSchemaShapeType<IAuth>
>({
  email,
  password,
});

export const validationSchemaTwoPassword = Yup.object().shape<
  ValidationSchemaShapeType<ISignUp>
>({
  email,
  password,
  confirm_password: password.oneOf(
    [Yup.ref("password")],
    VALIDATION_MESSAGES.repeat("Passwords")
  ),
});

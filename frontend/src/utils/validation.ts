import type Yup from "yup";

export type ValidationSchemaShapeType<
  KeyType extends string | number | symbol | object
> = Partial<
  Record<KeyType extends object ? keyof KeyType : KeyType, Yup.Schema>
>;

export const VALIDATION_MESSAGES = {
  required: "Required!",
  min: (num: number) => `Mininum ${num} characters!`,
  max: (num: number) => `Maximum ${num} characters!`,
  repeat: (fields: string) => `${fields} not match!`,
  unique: (field: string) => `${field} already exists!`,
};

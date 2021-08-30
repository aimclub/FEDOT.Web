export type OnChangeFormikType = {
  (e: React.ChangeEvent<any>): void;
  <T_1 = string | React.ChangeEvent<any>>(
    field: T_1
  ): T_1 extends React.ChangeEvent<any>
    ? void
    : (e: string | React.ChangeEvent<any>) => void;
};

export type SetFieldValue = (
  field: string,
  value: any,
  shouldValidate?: boolean | undefined
) => Promise<void>;

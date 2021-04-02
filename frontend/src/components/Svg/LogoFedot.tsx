import React, { FC } from "react";

import { SvgIcon, SvgIconProps } from "@material-ui/core";

const LogoFedot: FC<SvgIconProps> = (props) => {
  return (
    <SvgIcon {...props}>
      <path d="M53 187H7V234H53V187Z" fill="white" />
      <path d="M118.5 19.5H17V83L176 203L118.5 19.5Z" fill="white" />
      <path d="M175 19.5H143L207.5 230H227V72H201V47H175V19.5Z" fill="white" />
      <path d="M193 34.5V8.5H219V34.5H246V60.5H219V34.5H193Z" fill="white" />
      <path d="M227 26.5V0H253.5V26.5H227Z" fill="white" />
      <path d="M158 312V277H194V312H158Z" fill="white" />
      <path
        d="M0 314.5V263.5H34V268.5H15V286H31.5V291H15V314.5H0Z"
        fill="white"
      />
      <path
        d="M38.5 314.5V263.5H72V268.5H52.5V284.5H68V290H52.5V309.5H74.5V314.5H38.5Z"
        fill="white"
      />
      <path
        d="M149.5 267.5V262C149.5 262 128.5 267.5 128.5 294.5C128.5 321.5 149.5 328.5 149.5 328.5V325C149.5 325 140 315.5 140 294.5C140 273.5 149.5 267.5 149.5 267.5Z"
        fill="white"
      />
      <path
        d="M202.5 262V267.5C202.5 267.5 213 271.5 213 294.5C213 317.5 202.5 325 202.5 325V328.5C202.5 328.5 224.5 318 224.5 294.5C224.5 271 202.5 262 202.5 262Z"
        fill="white"
      />
      <path
        d="M240 314.5V268.5H227V263.5H269V268.5H256.5V314.5H240Z"
        fill="white"
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M79.5 263.5V314.5H105.5C105.5 314.5 123 313.5 123 288.5C123 263.5 105.5 263.5 105.5 263.5H79.5ZM94.5 310.5V267.5H101C101 267.5 108 270 108 288.5C108 307 101 310.5 101 310.5H94.5Z"
        fill="white"
      />
      <path d="M17 109.5L175 230H61V179H17V109.5Z" fill="white" />
    </SvgIcon>
  );
};

export default LogoFedot;

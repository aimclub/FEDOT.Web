import React from "react";
import style from "./logoFedot.module.scss";

type LogoFedotProps = {
  isLoading: boolean;
};

const LogoFedot = (props: LogoFedotProps) => {
  return (
    <svg viewBox="0 0 269 329" style={{ width: 50 }} className={style.root}>
      <g>
        <path d="M53 187H7v47h46v-47z" />
        <path
          className={props.isLoading ? style.triangleAnimation : ""}
          d="M118.5 19.5H17V83l159 120-57.5-183.5z"
        />
        <path d="M175 19.5h-32L207.5 230H227V72h-26V47h-26V19.5z" />
        <path d="M17 109.5L175 230H61v-51H17v-69.5z" />
      </g>
      <g>
        <path d="M193 34.5v-26h26v26h27v26h-27v-26h-26z" />
        <path d="M227 26.5V0h26.5v26.5H227z" />
      </g>
      <g className={props.isLoading ? style.nameAnimation : ""}>
        <path d="M158 312.5v-35h36v35h-36z" />
        <path d="M0 314.5v-51h34v5H15V286h16.5v5H15v23.5H0z" />
        <path d="M38.5 314.5v-51H72v5H52.5v16H68v5.5H52.5v19.5h22v5h-36z" />
        <path d="M149.5 268v-5.5s-21 5.5-21 32.5 21 34 21 34v-3.5S140 316 140 295s9.5-27 9.5-27z" />
        <path d="M202.5 262.5v5.5s10.5 4 10.5 27-10.5 30.5-10.5 30.5v3.5s22-10.5 22-34-22-32.5-22-32.5z" />
        <path d="M240 315v-46h-13v-5h42v5h-12.5v46H240z" />
        <path
          fillRule="evenodd"
          d="M79.5 263.5v51h26s17.5-1 17.5-26-17.5-25-17.5-25h-26zm15 47v-43h6.5s7 2.5 7 21-7 22-7 22h-6.5z"
          clipRule="evenodd"
        />
      </g>
    </svg>
  );
};

export default LogoFedot;

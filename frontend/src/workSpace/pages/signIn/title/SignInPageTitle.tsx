import scss from "./signInPageTitle.module.scss";

import Logo from "../../../../data/images/Logo.svg";

const SignInPageTitle = () => {
  return (
    <div className={scss.root}>
      <img src={Logo} alt="fedot" />
      <p className={scss.text}>FEDOT</p>
    </div>
  );
};

export default SignInPageTitle;

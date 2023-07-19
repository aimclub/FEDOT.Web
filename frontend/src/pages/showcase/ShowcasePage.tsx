import scss from "./showcasePage.module.scss";

import ShowcaseCases from "./cases/ShowcaseCases";
import ShowcaseInfo from "./info/ShowcaseInfo";

const ShowCase = () => {
  return (
    <div className={scss.root}>
      <ShowcaseInfo />
      <ShowcaseCases />
    </div>
  );
};

export default ShowCase;

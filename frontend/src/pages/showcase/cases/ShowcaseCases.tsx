import scss from "./showcaseCases.module.scss";

import Fade from "@mui/material/Fade";

import { showcaseAPI } from "../../../API/showcase/showcaseAPI";
import ShowcaseCasesCard from "./card/ShowcaseCasesCard";

const ShowcaseCases = () => {
  const { data: cases } = showcaseAPI.useGetAllShowcasesQuery(undefined);

  return (
    <Fade in={!!cases} mountOnEnter unmountOnExit timeout={2000}>
      <section className={scss.root}>
        <h2 className={scss.title}>Case</h2>
        <div className={scss.cases}>
          {cases?.map((showcase) => (
            <ShowcaseCasesCard key={showcase.case_id} showcase={showcase} />
          ))}
        </div>
      </section>
    </Fade>
  );
};

export default ShowcaseCases;

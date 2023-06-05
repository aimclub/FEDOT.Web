import scss from "./showcaseInfo.module.scss";

import { useEffect } from "react";

import Fade from "@mui/material/Fade";
import { useDispatch } from "react-redux";
import { Link } from "react-router-dom";

import { staticAPI } from "../../../API/baseURL";
import { showcaseAPI } from "../../../API/showcase/showcaseAPI";
import { useAppSelector } from "../../../hooks/redux";
import { setSelectedShowcase } from "../../../redux/showCase/showcaseSlice";
import { goToPage } from "../../../router/routes";
import { cl } from "../../../utils/classnames";
import ShowcaseInfoDetails from "./details/ShowcaseInfoDetails";

const ShowcaseInfo = () => {
  const dispatch = useDispatch();
  const { selected_showcase_id } = useAppSelector((state) => state.showcase);

  const {
    data: showcase,
    isFetching,
    isError,
  } = showcaseAPI.useGetShowcaseQuery(
    { caseId: selected_showcase_id },
    { skip: !selected_showcase_id }
  );

  useEffect(() => {
    if (isError) dispatch(setSelectedShowcase({ caseId: "" }));
  }, [dispatch, isError]);

  return (
    <section className={cl(scss.root, !selected_showcase_id && scss.hidden)}>
      {!isFetching ? (
        <Fade in={!isFetching} timeout={1000}>
          <div className={scss.paper}>
            <h2 className={scss.title}>{showcase?.title}</h2>
            <div className={scss.info}>
              <p className={scss.subTitle}>Model structure</p>
              <p className={scss.subTitle}>Model details</p>
              <img
                src={staticAPI.getImage(showcase?.icon_path || "")}
                alt={showcase?.title}
                className={scss.image}
              />

              <ShowcaseInfoDetails details={showcase?.details || {}} />

              <p className={scss.description}>{showcase?.description}</p>

              <div className={scss.bottom}>
                <Link
                  to={goToPage.sandbox(selected_showcase_id)}
                  className={scss.link}
                >
                  Edit in Sandbox
                </Link>
              </div>
            </div>
          </div>
        </Fade>
      ) : (
        <></>
      )}
    </section>
  );
};

export default ShowcaseInfo;

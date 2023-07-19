import scss from "./sandboxCharts.module.scss";

import { FC } from "react";

import { Link } from "react-router-dom";
import Paper from "@mui/material/Paper";

import { goToPage } from "../../../router/routes";
import SandboxChartsMetric from "./metric/SandboxChartsMetric";
import SandboxChartsResult from "./result/SandboxChartsResult";

const SandboxCharts: FC = () => {
  return (
    <section className={scss.root}>
      <div className={scss.top}>
        <Link to={goToPage.history()} className={scss.link}>
          History
        </Link>
      </div>
      <div className={scss.content}>
        <Paper className={scss.paper} component="article" elevation={3}>
          <h3 className={scss.subtitle}>Modeling Result</h3>
          <SandboxChartsResult classes={scss} />
        </Paper>
        <Paper className={scss.paper} component="article" elevation={3}>
          <h3 className={scss.subtitle}>Metric</h3>
          <SandboxChartsMetric classes={scss} />
        </Paper>
      </div>
    </section>
  );
};

export default SandboxCharts;

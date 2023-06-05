import Paper from "@mui/material/Paper";
import scss from "./authPage.module.scss";
import { Suspense } from "react";
import { Outlet } from "react-router-dom";

const AuthPage = () => {
  return (
    <main className={scss.root}>
      <div className={scss.logo} />
      <Paper className={scss.paper} component="section" elevation={3}>
        <Suspense>
          <Outlet />
        </Suspense>
      </Paper>
    </main>
  );
};

export default AuthPage;

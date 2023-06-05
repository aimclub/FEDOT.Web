import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { useAppSelector } from "../hooks/redux";
import { AppRoutesEnum, goToPage } from "./routes";

const AuthPage = lazy(() => import("../pages/auth/AuthPage"));
const SignInPage = lazy(() => import("../pages/auth/signIn/SignInPage"));
const SignUpPage = lazy(() => import("../pages/auth/signUp/SignUpPage"));

const WorkSpace = lazy(() => import("../components/WorkSpace/WorkSpace"));
const ShowcasePage = lazy(() => import("../pages/showcase/ShowcasePage"));
const SandboxPage = lazy(() => import("../pages/sandbox/SandboxPage"));
const HistoryPage = lazy(() => import("../pages/history/HistoryPage"));

const AppRouter = () => {
  const { isAuth } = useAppSelector((state) => state.auth);
  return (
    <Suspense>
      <Routes>
        <Route path={`${AppRoutesEnum.WORKSPACE}/*`} element={<WorkSpace />}>
          <Route path={AppRoutesEnum.SHOWCASE} element={<ShowcasePage />} />
          <Route path={`${AppRoutesEnum.SANDBOX}/${AppRoutesEnum.CASE}`}>
            <Route index element={<SandboxPage />} />
            <Route path={AppRoutesEnum.HISTORY} element={<HistoryPage />} />
          </Route>
          <Route path={AppRoutesEnum.SETTING} element={<p>settings</p>} />

          <Route path="*" element={<Navigate to={AppRoutesEnum.SHOWCASE} />} />
        </Route>
        <Route path="*" element={<Navigate to={goToPage.showcase} />} />

        {!isAuth && (
          <Route path={AppRoutesEnum.SIGNIN} element={<AuthPage />}>
            <Route index element={<SignInPage />} />
            <Route path={AppRoutesEnum.SIGNUP} element={<SignUpPage />} />
            <Route path="*" element={<Navigate to={AppRoutesEnum.SIGNIN} />} />
          </Route>
        )}
      </Routes>
    </Suspense>
  );
};

export default AppRouter;

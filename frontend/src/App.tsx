import React from "react";
import { BrowserRouter, Route, Switch } from "react-router-dom";

import "typeface-open-sans";
import "typeface-roboto";

import WorkSpace from "./components/WorkSpace/WorkSpace";
import SignInPage from "./pages/signIn/SignInPage";
import { AppRoutesEnum } from "./routes";

function App() {
  return (
    <BrowserRouter>
      <Switch>
        <Route
          exact
          path={[AppRoutesEnum.SIGNIN, AppRoutesEnum.SIGNUP]}
          component={SignInPage}
        />
        <WorkSpace />
      </Switch>
    </BrowserRouter>
  );
}

export default App;

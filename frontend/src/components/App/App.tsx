import React from "react";
import "./App.scss";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import SideMenu from "../SideMenu/SideMenu";
import Sandbox from "../../pages/Sandbox/Sandbox";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import Showcase from "../../pages/Showcase/Showcase";
import History from "../../pages/History/History";

function App() {
  const theme = createMuiTheme({
    palette: {
      primary: {
        main: "#263238",
      },
      secondary: {
        main: "#2196F3",
      },
    },
  });

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <div className="App">
          <SideMenu />
          <Switch>
            <Route exact path="/">
              <Showcase />
            </Route>
            <Route exact path="/sandbox/:uid">
              <Sandbox />
            </Route>
            <Route exact path="/sandbox/history">
              <History />
            </Route>
            <Route exact path="/fedot">
              <History />
            </Route>
          </Switch>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

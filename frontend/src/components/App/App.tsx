import React, { useEffect, useState } from "react";
import "./App.scss";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import SideMenu from "../SideMenu/SideMenu";
import { useMediaQuery } from "@material-ui/core";
import Sandbox from "../../pages/Sandbox/Sandbox";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import Showcase from "../../pages/Showcase/Showcase";
import History from "../History/History";
import dataPopulation from "../../data/dataPopulation.json";
import dataCompose from "../../data/composeData.json";
import dataHistory from "../../data/responseHistory.json";
import { sandboxAPI } from "../../api/sandbox";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const [isDark, setDark] = useState(false);

  const changeTheme = () => {
    setDark(!isDark);
  };

  const theme = React.useMemo(
    () =>
      createMuiTheme({
        palette: {
          type: isDark ? "dark" : "light",
          primary: {
            main: isDark ? "#0199E4" : "#263238",
          },
          secondary: {
            main: isDark ? "##BB86FC" : "#2196F3",
          },
        },
      }),
    [isDark]
  );
  useEffect(() => {
    prefersDarkMode ? setDark(true) : setDark(false);
  }, [prefersDarkMode]);

  return (
    <ThemeProvider theme={theme}>
      <BrowserRouter>
        <div className="App">
          <SideMenu changeTheme={changeTheme} />
          <Switch>
            <Route exact path="/">
              <Showcase />
            </Route>
            <Route exact path="/sandbox">
              <Sandbox />
            </Route>
            <Route exact path="/sandbox/history">
              <History
                edgesData={dataHistory.edges}
                nodesData={dataHistory.nodes}
                onClick={() => {
                  console.log("handleClick");
                }}
              />
            </Route>
          </Switch>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

import React, { useEffect, useState } from "react";
import "./App.scss";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import SideMenu from "../SideMenu/SideMenu";
import { useMediaQuery } from "@material-ui/core";
import Sandbox from "../../pages/Sandbox/Sandbox";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import Showcase from "../../pages/Showcase/Showcase";
import History from "../History/History";
import { useDispatch, useSelector } from "react-redux";
import { getHistoryGraph } from "../../store/sandbox-reducer";
import { StateType } from "../../store/store";
// import historyGraph from "../../data/responseHistory.json";

function App() {
  const dispatch = useDispatch();
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const [isDark, setDark] = useState(false);

  const nodeHoverTooltip = React.useCallback((node) => {
    return `<div>     
      <p >${node}</p>
    </div>`;
  }, []);

  const { historyGraph } = useSelector(
    (state: StateType) => state.sandboxReducer
  );

  const changeTheme = () => {
    setDark(!isDark);
  };

  useEffect(() => {
    dispatch(getHistoryGraph(45454));
  }, [dispatch]);

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
            <Route exact path="/fedot">
              <History
                edgesData={historyGraph.edges}
                nodesData={historyGraph.nodes}
                onClick={() => {
                  console.log("handleClick");
                }}
                nodeHoverTooltip={nodeHoverTooltip}
              />
            </Route>
          </Switch>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

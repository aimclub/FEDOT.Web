import React, { useEffect, useState } from "react";
import "./App.css";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import SideMenu from "./components/Drawer";
import { ForceGraph } from "./components/ForceGraph";
import data from "./data/data.json";
import { Paper, useMediaQuery } from "@material-ui/core";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const [isDark, setDark] = useState(false);

  const nodeHoverTooltip = React.useCallback((node) => {
    console.log(`### nodeHoverTooltip: none`, node);
    return (
      <div>
        <p>kek</p>
      </div>
    );
  }, []);

  const onClick = (d: any) => {
    console.log(`### d`, d);
  };

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
      <SideMenu changeTheme={changeTheme} />
      <div style={{ display: "flex", flexDirection: "column", marginLeft: 80 }}>
        <Paper style={{ margin: 8 }} elevation={3}>
          <div>s</div>
        </Paper>
        <Paper elevation={3} style={{ margin: 8 }}>
          <ForceGraph
            edgesData={data.edges}
            nodesData={data.nodes}
            nodeHoverTooltip={nodeHoverTooltip}
            onClick={onClick}
          />
        </Paper>
        <Paper elevation={3} style={{ margin: 8 }}>
          <div>s</div>
        </Paper>
        <Paper elevation={3} style={{ margin: 8 }}>
          <div>s</div>
        </Paper>
      </div>
    </ThemeProvider>
  );
}

export default App;

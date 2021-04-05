import React, { useEffect, useState } from "react";
import "./App.scss";
import { createMuiTheme, ThemeProvider } from "@material-ui/core/styles";
import SideMenu from "./components/Drawer";
import { useMediaQuery } from "@material-ui/core";
import Sandbox from "./pages/Sandbox";
import clsx from "clsx";

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
      <div className={clsx("App", isDark ? "dark" : "")}>
        <SideMenu changeTheme={changeTheme} />
        <Sandbox />
      </div>
    </ThemeProvider>
  );
}

export default App;

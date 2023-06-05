import MiniCssExtractPlugin from "mini-css-extract-plugin";
import autoprefixer from "autoprefixer";
import parserComment from "postcss-scss";
import { RuleSetRule, RuleSetUseItem } from "webpack";

const styleLoader = (isDev: boolean): RuleSetRule => {
  const use: RuleSetUseItem[] = isDev
    ? ["style-loader", "@teamsupercell/typings-for-css-modules-loader"]
    : [MiniCssExtractPlugin.loader];

  return {
    test: /\.(s[ac]|c)ss$/i,
    use: [
      ...use,
      {
        loader: "css-loader",
        options: {
          modules: {
            auto: (resourcePath: string) =>
              resourcePath.endsWith(".module.scss"),
            localIdentName: isDev
              ? "[path][name]__[local]--[hash:base64:4]"
              : "[hash:base64:8]",
          },
        },
      },
      {
        loader: "resolve-url-loader",
        options: {
          sourceMap: true,
          debug: true,
          silent: true,
        },
      },
      {
        loader: "sass-loader",
        options: {
          sourceMap: true,
        },
      },
      {
        loader: "postcss-loader",
        options: {
          sourceMap: true,
          postcssOptions: {
            parser: parserComment,
            plugins: [isDev ? "" : autoprefixer()],
          },
        },
      },
    ],
  };
};

export default styleLoader;

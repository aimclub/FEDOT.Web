import { RuleSetRule } from "webpack";
import styleLoader from "./loaders/styleLoader";
import { IOptions } from "./types";

export const buildLoaders = ({ isDev }: IOptions): RuleSetRule[] => {
  const typescriptLoader = {
    test: /\.(ts|js)x?$/,
    exclude: /node_modules/,
    use: [{ loader: "babel-loader" }],
  };

  const svgLoader = {
    test: /\.svg$/,
    use: ["@svgr/webpack"],
  };

  const imagesLoader = {
    test: /\.(ico|jpg|jpeg|png|gif)(\?.*)?$/,
    type: "asset/resource",
  };

  const fontsLoader = {
    test: /\.(eot|otf|webp|ttf|woff|woff2)(\?.*)?$/,
    type: "asset/resource",
    generator: {
      filename: "fonts/[hash][ext][query]",
    },
  };

  return [
    typescriptLoader,
    styleLoader(isDev),
    svgLoader,
    imagesLoader,
    fontsLoader,
  ];
};

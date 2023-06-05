declare module "*.png";
declare module "*.jpg";
declare module "*.jpeg";

declare module "*.svg" {
  const SVG: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default SVG;
}

import * as d3 from "d3";
import "./History.module.scss";
import dagreD3 from "dagre-d3";

export function runHistory(container, linksData, nodesData) {
  let links = linksData.map((d) => Object.assign({}, d));
  let nodes = nodesData.map((d) => Object.assign({}, d));

  const containerRect = container.getBoundingClientRect();
  const height = containerRect.height;
  const width = containerRect.width;

  const svg = d3
    .select(container)
    .append("svg")
    .attr("id", "graphSvg")
    .attr("viewBox", [-width / 2, -height / 2, width, height])
    .call(
      d3.zoom().on("zoom", function (event) {
        svgGroup.attr("transform", event.transform);
      })
    );

  // Set up an SVG group so that we can translate the final graph.
  let svgGroup = svg.append("g");

  // Create the input graph
  let g = new dagreD3.graphlib.Graph({ compound: true, multigraph: true })
    .setGraph({ rankdir: "TB" })
    .setDefaultEdgeLabel(() => ({}));

  // Here we're setting nodeclass, which is used by our custom drawNodes function
  // below.

  //TODO: Кластеры поколений
  g.setNode("generationsAll", {
    label: "generation0",
    clusterLabelPos: "top",
    style: "fill: #E6399B",
  });
  g.setNode("generation0", {
    label: "generation0",
    clusterLabelPos: "top",
    style: "fill: #d3d7e8",
  });
  g.setNode("generation1", {
    label: "generation1",
    clusterLabelPos: "top",
    style: "fill: #ffd47f",
  });
  g.setNode("generation2", { label: "generation2", style: "fill: #5f9488" });

  nodes.forEach((item) => {
    // let label = item.display_name;
    g.setNode(item.uid, {
      label: item.uid,
      class: item.type === "evo_operator" ? "type-TOP" : "type-TK",
      shape: item.type === "evo_operator" ? "circle" : "rect",
    });

    g.setParent("generation0", "generationsAll");
    g.setParent("generation1", "generationsAll");

    if (item.uid.includes("_0_")) {
      console.log(`### item.uid`, item.uid);
      g.setParent(item.uid, "generation0");
    }
    if (item.uid.includes("_1_")) {
      console.log(`### item.uid`, item.uid);
      g.setParent(item.uid, "generation1");
    }
    if (item.uid.includes("_2_")) {
      console.log(`### item.uid`, item.uid);
      g.setParent(item.uid, "generation2");
    }
  });

  g.nodes().forEach(function (v) {
    let node = g.node(v);
    // Round the corners of the nodes
    node.rx = node.ry = 5;
  });

  // Set up edges, no special attributes.
  links.forEach((item) => {
    const haveSource = g.hasNode(item.source);
    const haveTarget = g.hasNode(item.target);
    if (haveSource && haveTarget) {
      if (item.source < 8) {
        g.setEdge(item.source, item.target, {
          // arrowheadStyle: "fill: gold",
          // style: "stroke: #gold; stroke-width: 3px;",
          // class: item.source < 5 ? "edge-ONE" : "edge-TWO",
        });
      } else {
        g.setEdge(item.source, item.target, {
          // arrowheadStyle: "fill: #f66",
          // style: "stroke: #f66; stroke-width: 3px; stroke-dasharray: 5, 5;",
        });
      }
    }
  });

  // Create the renderer
  let render = new dagreD3.render();

  // Run the renderer. This is what draws the final graph.
  render(svgGroup, g);

  // Center the graph
  const gHeight = g.graph().height;
  const gWidth = g.graph().width;
  let xCenterOffset = (svg.attr("width") - gWidth) / 2;
  let yCenterOffset = (svg.attr("height") - gHeight) / 2;

  if (height < gHeight || width < gWidth) {
    const viewHeight = height < gHeight ? gHeight : height;
    const viewWidth = width < gWidth ? gWidth : width;

    svg.attr("viewBox", [
      -viewWidth / 2,
      -viewHeight / 2,
      viewWidth,
      viewHeight,
    ]);
  }
  svgGroup.attr(
    "transform",
    "translate(" + xCenterOffset + "," + yCenterOffset + ")"
  );

  return {
    destroy: () => {
      return svg.remove();
    },
    nodes: () => {
      return svg.node();
    },
  };
}

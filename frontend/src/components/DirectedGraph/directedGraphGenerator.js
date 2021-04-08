import * as d3 from "d3";
import "./directedGraph.module.scss";
import dagreD3 from "dagre-d3";

export function runDirectedGraph(container, linksData, nodesData) {
  let links = linksData.map((d) => Object.assign({}, d));
  let nodes = nodesData.map((d) => Object.assign({}, d));

  const containerRect = container.getBoundingClientRect();
  const height = containerRect.height;
  const width = containerRect.width;

  console.log(`### height`, height);
  console.log(`### width`, width);

  const svg = d3
    .select(container)
    .append("svg")
    .attr("id", "graphSvg")
    .attr("viewBox", [-width / 2, -height / 2, width, height])
    .call(
      d3.zoom().on("zoom", function (event) {
        svg.attr("transform", event.transform);
      })
    );

  // Create the input graph
  let g = new dagreD3.graphlib.Graph()
    .setGraph({ rankdir: "LR" })
    .setDefaultEdgeLabel(() => ({}));
  // Here we're setting nodeclass, which is used by our custom drawNodes function
  // below.
  nodes.forEach((item) => {
    let label = item.display_name;

    g.setNode(item.id, {
      label: label,
      class: item.id < 5 ? "type-TOP" : "type-TK",
    });
  });

  g.nodes().forEach(function (v) {
    let node = g.node(v);

    // Round the corners of the nodes
    node.rx = node.ry = 5;
  });

  // Set up edges, no special attributes.
  links.forEach((item) => {
    const haveSource = nodes.find((elem) => elem.id === item.source);
    const haveTarget = nodes.find((elem) => elem.id === item.target);
    if (haveSource && haveTarget) {
      g.setEdge(item.source, item.target);
    }
  });

  // Create the renderer
  let render = new dagreD3.render();

  // // // Set up an SVG group so that we can translate the final graph.
  let svgGroup = d3.select("#graphSvg");

  // Run the renderer. This is what draws the final graph.
  render(svgGroup, g);

  // Center the graph
  console.log(`### g.graph().width`, g.graph().width);
  let xCenterOffset = (svg.attr("width") - g.graph().width) / 2;
  let yCenterOffset = (svg.attr("height") - g.graph().height) / 2;
  console.log(`### xCenterOffset`, xCenterOffset);
  console.log(`### yCenterOffset`, yCenterOffset);
  svgGroup.attr(
    "transform",
    "translate(" + xCenterOffset + "," + yCenterOffset + ")"
  );

  const addNode = (event, d) => {
    const id = g.nodes().length;
    console.log(`### nodes.length`, nodes.length);
    console.log(`### g.nodes().length`, g.nodes().length);
    g.setNode(id, {
      label: "NEW",
      class: "type-NEW",
    });
    console.log(`### g.node(id)`, g.node(id));
    let node = g.node(id);
    Array.from(node, (el) => el.addEventListener("click", addNode));
    g.setEdge(id, d);
    console.log(`### d`, d);
    render(svgGroup, g);
  };

  svgGroup.selectAll("g.node").on("click", addNode);

  return {
    destroy: () => {
      return svg.remove();
    },
    nodes: () => {
      return svg.node();
    },
  };
}

/* eslint-disable @typescript-eslint/no-explicit-any */
// TODO: any in createHistoryGraph

import * as d3 from "d3";
import dagreD3 from "dagre-d3";
import {
  IHistoryEdge,
  IHistoryNodeIndividual,
  IHistoryNodeOperator,
} from "../API/composer/composerInterface";

// TODO: refactor createHistoryGraph

export type ZoomType = { x: number; y: number; k: number } | undefined;

export const createHistoryGraph = (
  container: HTMLDivElement,
  linksData: IHistoryEdge[],
  nodesData: (IHistoryNodeIndividual | IHistoryNodeOperator)[],
  highlightNodes: string[],
  onClickPipeline: (value: IHistoryNodeIndividual) => void,
  onDblClickPipeline: (value: IHistoryNodeIndividual) => void,
  { zoom, setZoom }: { zoom: ZoomType; setZoom: (v: ZoomType) => void }
) => {
  const links = linksData.map((d) => ({ ...d }));
  const nodesIndividual = nodesData.filter(
    (item) => item.type === "individual"
  ) as IHistoryNodeIndividual[];
  const nodesOperator = nodesData.filter(
    (item) => item.type === "evo_operator"
  ) as IHistoryNodeOperator[];

  const uniqGenerations = Array.from(
    new Set(nodesIndividual.map((item) => item.gen_id))
  );

  const { height, width } = container.getBoundingClientRect();

  const svg = d3
    .select(container)
    .append("svg")
    .attr("class", "history-graph")
    .attr("viewBox", [-width / 2, -height / 2, width, height])
    .call(
      d3.zoom().on("zoom", function (event) {
        svgGroup.attr("transform", event.transform);
        // console.log(event.transform);
        setZoom(event.transform as ZoomType);
      }) as any
    );

  const svgGroup = svg
    .append("g")
    .on("click", (event) => {
      if (event.target) {
        event.stopPropagation();
        const node = nodesIndividual.find(
          (item) => item.uid === event.target.textContent
        );
        if (node) onClickPipeline(node);
      }
    })
    .on("dblclick", (event) => {
      if (event.target) {
        event.stopPropagation();
        const node = nodesIndividual.find(
          (item) => item.uid === event.target.textContent
        );
        if (node) onDblClickPipeline(node);
      }
    });

  const g = new dagreD3.graphlib.Graph({ compound: true })
    .setGraph({
      rankdir: "TB",
      ranker: "network-simplex",
      align: "DL",
    })
    .setDefaultEdgeLabel(() => ({}));

  uniqGenerations.forEach((generation) => {
    const nameG = `Generation ${generation}`;

    g.setNode(`${generation}`, {
      label: generation,
      labelStyle: "cursor: default;",
      clusterLabelPos: "left",
      style: "fill: #d3d7e8; cursor: default;",
    });
    g.setNode(nameG, {
      label: nameG,
    });
    g.setParent(nameG, String(generation));

    nodesIndividual.forEach((item) => {
      if (generation === item.gen_id) {
        g.setNode(item.uid, {
          label: item.uid,
          labelStyle: "font-size: 36px; cursor: pointer;",
          class: `type-TK ${highlightNodes.includes(item.uid) && "highlight"}`,
          shape: "rect",
        });

        g.setParent(item.uid, String(generation));
      }
    });
  });

  nodesOperator.forEach((item) => {
    const label = item.name[0][0].toUpperCase();
    g.setNode(item.uid, {
      label: label,
      labelStyle: "font-size: 60px; cursor: default;",
      class: `operator-${label} ${
        highlightNodes.includes(item.uid) && "highlight"
      }`,
      shape: "circle",
    });
  });

  g.nodes().forEach(function (v) {
    const node = g.node(v);
    // Round the corners of the nodes
    node.rx = node.ry = 5;
  });

  // Set up edges, no special attributes.
  links.forEach((item) => {
    const haveSource = g.hasNode(item.source);
    const haveTarget = g.hasNode(item.target);
    if (haveSource && haveTarget) {
      g.setEdge(item.source, item.target, {
        // style: "stroke: #007DFF; stroke-width: 4px; fill-opacity: 0",
        // arrowheadStyle: "fill: #007DFF",
        curve: d3.curveBasis,
        class: `${
          highlightNodes.includes(item.source) &&
          highlightNodes.includes(item.target) &&
          "highlight"
        }`,
      });
    }
  });

  // Create the renderer
  const render = new dagreD3.render();

  // Run the renderer. This is what draws the final graph.
  render(svgGroup as any, g as any);

  // Center the graph
  const gHeight = (g.graph() as any).height;
  const gWidth = (g.graph() as any).width;

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

  if (!zoom) {
    const xCenterOffset = (+svg.attr("width") - gWidth) / 2;
    const yCenterOffset = (+svg.attr("height") - gHeight) / 2;

    svgGroup.attr(
      "transform",
      "translate(" + xCenterOffset + "," + yCenterOffset + ")"
    );
  } else {
    svgGroup.attr(
      "transform",
      `translate(${zoom.x},${zoom.y}) scale(${zoom.k})`
    );
  }

  /**
   * Блок добавления и удаления подсказки на Граф
   */
  // const tooltip = document.querySelector("#graph-tooltip");
  // if (!tooltip) {
  //   const tooltipDiv = document.createElement("div");
  //   tooltipDiv.classList.add(styles.tooltip);
  //   tooltipDiv.style.opacity = "0";
  //   tooltipDiv.id = "graph-tooltip";
  //   document.body.appendChild(tooltipDiv);
  // }
  // const div = d3.select("#graph-tooltip");

  // //показать рядом с нужным Узлом
  // const addTooltip = (hoverTooltip, d, x, y) => {
  //   div.transition().duration(200).style("opacity", 0.9);
  //   div
  //     .html(hoverTooltip(d))
  //     .style("left", `${x}px`)
  //     .style("top", `${y - 28}px`);
  // };
  // //скрыть
  // const removeTooltip = () => {
  //   div.transition().duration(200).style("opacity", 0);
  // };
  /**
   * Конец блока добавления и удаления Подсказки
   */

  // svgGroup.selectAll("g.node");
  // .on("mouseover", (event, d) => {
  //   addTooltip(nodeHoverTooltip, d, event.pageX, event.pageY);
  // })
  // .on("mouseout", () => {
  //   removeTooltip();
  // });

  return {
    destroy: () => {
      svg.remove();
    },
    nodes: () => {
      return svg.node();
    },
  };
};

import dagre from '@dagrejs/dagre'
import { Position, type Edge, type Node, type NodeHandle } from '@xyflow/react'

export const NODE_WIDTH = 220

/** Header, category chip and padding, before any hyperparameter rows. */
const NODE_HEADER_HEIGHT = 78

/** One hyperparameter row on the card. */
const PARAM_ROW_HEIGHT = 16

/** Rows shown on a card before the rest collapse into a "+N more" line. */
export const MAX_VISIBLE_PARAMS = 4

/** Height grows with the number of hyperparameter rows shown on the node. */
export const nodeHeight = (paramCount: number): number => {
  const rows = Math.min(paramCount, MAX_VISIBLE_PARAMS)
  const overflowRow = paramCount > MAX_VISIBLE_PARAMS ? PARAM_ROW_HEIGHT : 0
  return NODE_HEADER_HEIGHT + rows * PARAM_ROW_HEIGHT + overflowRow
}

export type LayoutDirection = 'LR' | 'TB'

/** Size of the connection dots drawn by `PipelineNodeCard`. */
const HANDLE_SIZE = 9

/**
 * Where the connection points sit on a node of the given size.
 *
 * React Flow normally discovers this by measuring the handle elements once they
 * are on screen, and refuses to route an edge until it has. Declaring the
 * geometry up front — it is fixed by the card's own layout — means the edges are
 * drawn on the first render instead of appearing a frame later, and it keeps the
 * graph correct in contexts where the resize observer never fires.
 */
const handlesFor = (height: number, direction: LayoutDirection): NodeHandle[] => {
  const horizontal = direction === 'LR'
  const offset = HANDLE_SIZE / 2
  return [
    {
      type: 'target',
      position: horizontal ? Position.Left : Position.Top,
      x: horizontal ? -offset : NODE_WIDTH / 2 - offset,
      y: horizontal ? height / 2 - offset : -offset,
      width: HANDLE_SIZE,
      height: HANDLE_SIZE,
    },
    {
      type: 'source',
      position: horizontal ? Position.Right : Position.Bottom,
      x: horizontal ? NODE_WIDTH - offset : NODE_WIDTH / 2 - offset,
      y: horizontal ? height / 2 - offset : height - offset,
      width: HANDLE_SIZE,
      height: HANDLE_SIZE,
    },
  ]
}

/**
 * Position nodes with dagre.
 *
 * FEDOT pipelines flow from data sources to the root predictor, so the default
 * is left-to-right; forecasting pipelines with long preprocessing chains read
 * better top-to-bottom, hence the toggle.
 */
export function layoutGraph<N extends Node, E extends Edge>(
  nodes: N[],
  edges: E[],
  direction: LayoutDirection = 'LR',
): N[] {
  if (nodes.length === 0) return nodes

  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({
    rankdir: direction,
    nodesep: direction === 'LR' ? 28 : 48,
    ranksep: direction === 'LR' ? 96 : 72,
    marginx: 24,
    marginy: 24,
  })

  for (const node of nodes) {
    const params = (node.data as { paramCount?: number })?.paramCount ?? 0
    graph.setNode(node.id, { width: NODE_WIDTH, height: nodeHeight(params) })
  }
  for (const edge of edges) {
    if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
      graph.setEdge(edge.source, edge.target)
    }
  }

  dagre.layout(graph)

  return nodes.map((node) => {
    const positioned = graph.node(node.id)
    if (!positioned) return node
    const params = (node.data as { paramCount?: number })?.paramCount ?? 0
    const height = nodeHeight(params)
    return {
      ...node,
      // dagre reports the centre; React Flow positions by the top-left corner.
      position: { x: positioned.x - NODE_WIDTH / 2, y: positioned.y - height / 2 },
      // Declaring the size explicitly means React Flow does not have to wait for
      // a ResizeObserver before it can route the edges, so the graph is complete
      // on first paint instead of appearing node-by-node.
      width: NODE_WIDTH,
      height,
      handles: handlesFor(height, direction),
      targetPosition: direction === 'LR' ? Position.Left : Position.Top,
      sourcePosition: direction === 'LR' ? Position.Right : Position.Bottom,
    } as N
  })
}

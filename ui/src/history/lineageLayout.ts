import { Position, type NodeHandle } from '@xyflow/react'

import type { LineageEdge, LineageNode } from '../api/types'

export const INDIVIDUAL_WIDTH = 150
export const INDIVIDUAL_HEIGHT = 54
export const OPERATOR_SIZE = 34

/** Vertical distance between one generation's row and the next. */
const LAYER_GAP = 110

/** Horizontal distance between neighbours in the same row. */
const COLUMN_GAP = 32

/**
 * Width of the label column to the left of the rows. Labels used to sit inside
 * the lane band, where a row wide enough to reach the left edge ran straight
 * under them; giving them their own gutter means nodes can never overlap text.
 */
export const LANE_LABEL_GUTTER = 176

/** Sweeps of the barycentre heuristic used to reduce edge crossings. */
const ORDERING_PASSES = 6

export interface PositionedLineageNode extends LineageNode {
  x: number
  y: number
  width: number
  height: number
  /** Declared so React Flow can route edges without measuring the DOM first. */
  handles: NodeHandle[]
}

/** Generations read top to bottom, so descent enters at the top and leaves at the bottom. */
const handlesFor = (width: number, height: number): NodeHandle[] => [
  { type: 'target', position: Position.Top, x: width / 2, y: 0, width: 1, height: 1 },
  { type: 'source', position: Position.Bottom, x: width / 2, y: height, width: 1, height: 1 },
]

export interface LineageLayout {
  nodes: PositionedLineageNode[]
  /** Row bands, one per generation, for the background lanes and labels. */
  lanes: { generation: number; y: number; height: number; isEmpty: boolean }[]
  width: number
  height: number
}

/** Height of a lane whose generation contributed nothing to the shown graph. */
const EMPTY_LANE_HEIGHT = 22

const sizeOf = (node: LineageNode) =>
  node.kind === 'operator'
    ? { width: OPERATOR_SIZE, height: OPERATOR_SIZE }
    : { width: INDIVIDUAL_WIDTH, height: INDIVIDUAL_HEIGHT }

/**
 * Lay the genealogy out in layers.
 *
 * The structure is already layered — generation `g` occupies layer `2g`, and the
 * operators that produced generation `g` sit on layer `2g-1` — so rather than
 * handing it to a general graph layout, the rows are placed directly and only
 * the order *within* each row is solved for. That keeps generations perfectly
 * aligned, which is the whole point of reading the graph top to bottom.
 *
 * Ordering uses the barycentre heuristic: repeatedly place each node at the mean
 * position of its neighbours in the adjacent layer, alternating direction. It is
 * the standard cheap way to cut edge crossings in a layered drawing.
 */
export function layoutLineage(
  nodes: LineageNode[],
  edges: LineageEdge[],
  /**
   * Every generation the run recorded. Generations that contributed nothing to
   * the shown graph still get a thin empty lane, so the numbering stays
   * continuous and "no ancestor of the winner lived here" is visible rather than
   * looking like a gap in the data.
   */
  allGenerations: number[] = [],
): LineageLayout {
  if (nodes.length === 0) {
    return { nodes: [], lanes: [], width: 0, height: 0 }
  }

  const byLayer = new Map<number, LineageNode[]>()
  for (const node of nodes) {
    const bucket = byLayer.get(node.layer) ?? []
    bucket.push(node)
    byLayer.set(node.layer, bucket)
  }
  const layers = [...byLayer.keys()].sort((a, b) => a - b)

  // Start from the order the backend produced, which follows population order.
  const order = new Map<number, string[]>()
  for (const layer of layers) {
    order.set(
      layer,
      byLayer.get(layer)!.map((node) => node.id),
    )
  }

  const parentsOf = new Map<string, string[]>()
  const childrenOf = new Map<string, string[]>()
  for (const edge of edges) {
    if (!parentsOf.has(edge.target)) parentsOf.set(edge.target, [])
    if (!childrenOf.has(edge.source)) childrenOf.set(edge.source, [])
    parentsOf.get(edge.target)!.push(edge.source)
    childrenOf.get(edge.source)!.push(edge.target)
  }

  const positionInLayer = new Map<string, number>()
  const refreshPositions = () => {
    for (const layer of layers) {
      order.get(layer)!.forEach((id, index) => positionInLayer.set(id, index))
    }
  }
  refreshPositions()

  const barycentre = (id: string, neighbours: Map<string, string[]>): number | null => {
    const linked = neighbours.get(id) ?? []
    const positions = linked
      .map((other) => positionInLayer.get(other))
      .filter((value): value is number => value !== undefined)
    if (positions.length === 0) return null
    return positions.reduce((sum, value) => sum + value, 0) / positions.length
  }

  for (let pass = 0; pass < ORDERING_PASSES; pass += 1) {
    const downward = pass % 2 === 0
    const sequence = downward ? layers : [...layers].reverse()
    const neighbours = downward ? parentsOf : childrenOf

    for (const layer of sequence) {
      const ids = order.get(layer)!
      const keys = new Map<string, number>()
      ids.forEach((id, index) => {
        // A node with no neighbour in the reference layer keeps its place.
        keys.set(id, barycentre(id, neighbours) ?? index)
      })
      const sorted = [...ids].sort((a, b) => keys.get(a)! - keys.get(b)!)
      order.set(layer, sorted)
    }
    refreshPositions()
  }

  const nodeById = new Map(nodes.map((node) => [node.id, node]))

  // Row widths decide the overall canvas width, so measure before placing.
  const rowWidths = new Map<number, number>()
  for (const layer of layers) {
    const width = order
      .get(layer)!
      .reduce((total, id) => total + sizeOf(nodeById.get(id)!).width + COLUMN_GAP, -COLUMN_GAP)
    rowWidths.set(layer, Math.max(width, 0))
  }
  const canvasWidth = Math.max(...rowWidths.values(), INDIVIDUAL_WIDTH)

  const positioned: PositionedLineageNode[] = []
  const laneByGeneration = new Map<number, { top: number; bottom: number }>()
  let y = 0

  // Walk generations in order, emitting the operator row that feeds each one and
  // then the generation itself — or a placeholder when nothing from it is shown.
  const highestGeneration = Math.max(
    ...layers.map((layer) => Math.ceil(layer / 2)),
    ...allGenerations,
    0,
  )
  const emptyGenerations = new Set<number>()

  type Row = { layer: number } | { emptyGeneration: number }
  const rows: Row[] = []
  for (let generation = 0; generation <= highestGeneration; generation += 1) {
    if (byLayer.has(generation * 2 - 1)) rows.push({ layer: generation * 2 - 1 })
    if (byLayer.has(generation * 2)) {
      rows.push({ layer: generation * 2 })
    } else if (allGenerations.includes(generation)) {
      rows.push({ emptyGeneration: generation })
      emptyGenerations.add(generation)
    }
  }

  for (const row of rows) {
    if ('emptyGeneration' in row) {
      laneByGeneration.set(row.emptyGeneration, { top: y, bottom: y + EMPTY_LANE_HEIGHT })
      y += EMPTY_LANE_HEIGHT + LAYER_GAP / 2
      continue
    }

    const ids = order.get(row.layer)!
    const rowHeight = Math.max(...ids.map((id) => sizeOf(nodeById.get(id)!).height))
    let x = (canvasWidth - rowWidths.get(row.layer)!) / 2

    for (const id of ids) {
      const node = nodeById.get(id)!
      const { width, height } = sizeOf(node)
      positioned.push({
        ...node,
        x,
        // Centre smaller nodes (the operator dots) within the row.
        y: y + (rowHeight - height) / 2,
        width,
        height,
        handles: handlesFor(width, height),
      })
      x += width + COLUMN_GAP
    }

    if (row.layer % 2 === 0) {
      laneByGeneration.set(row.layer / 2, { top: y - 10, bottom: y + rowHeight + 10 })
    }

    y += rowHeight + LAYER_GAP
  }

  const lanes = [...laneByGeneration.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([generation, band]) => ({
      generation,
      y: band.top,
      height: band.bottom - band.top,
      isEmpty: emptyGenerations.has(generation),
    }))

  return {
    nodes: positioned,
    lanes,
    width: canvasWidth,
    height: Math.max(y - LAYER_GAP, 0),
  }
}

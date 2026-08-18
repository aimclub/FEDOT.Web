import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'

import type { LineageGraph } from '../api/types'
import { LineageIndividualNode, LineageOperatorNode, operatorColor } from './LineageNodes'
import { LANE_LABEL_GUTTER, layoutLineage } from './lineageLayout'

/** Extra room around the lanes so the label has somewhere to sit. */
const LANE_PADDING = 28

const nodeTypes = {
  lineageIndividual: LineageIndividualNode,
  lineageOperator: LineageOperatorNode,
  generationLane: GenerationLane,
}

/** A labelled band behind one generation's row. */
function GenerationLane({
  data,
}: {
  data: { label: string; isEvolutionary: boolean; isEmpty: boolean; emptyReason: string }
}) {
  const theme = useTheme()

  const label = (
    <Box sx={{ width: LANE_LABEL_GUTTER - 14, flexShrink: 0, textAlign: 'right', pr: 1.5 }}>
      <Typography
        sx={{
          fontSize: '0.65rem',
          color: 'text.disabled',
          fontWeight: data.isEvolutionary && !data.isEmpty ? 700 : 500,
          fontStyle: data.isEvolutionary && !data.isEmpty ? 'normal' : 'italic',
        }}
      >
        {data.label}
      </Typography>
    </Box>
  )

  if (data.isEmpty) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          pointerEvents: 'none',
        }}
      >
        {label}
        <Box sx={{ flexGrow: 1, borderTop: '1px dashed', borderColor: 'divider' }} />
        <Typography sx={{ fontSize: '0.6rem', color: 'text.disabled', pr: 1, fontStyle: 'italic' }}>
          {data.emptyReason}
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', pointerEvents: 'none' }}>
      {label}
      <Box
        sx={{
          flexGrow: 1,
          height: '100%',
          borderRadius: 1,
          // The seed population is not a round of evolution, so its band is
          // dimmer than the generations that did the work.
          bgcolor: alpha(theme.palette.text.primary, data.isEvolutionary ? 0.045 : 0.02),
          border: '1px dashed',
          borderColor: theme.palette.divider,
        }}
      />
    </Box>
  )
}

interface Props {
  graph: LineageGraph
  selectedUid?: string | null
  onSelect?: (uid: string) => void
}

function Canvas({ graph, selectedUid, onSelect }: Props) {
  const theme = useTheme()
  const { fitView } = useReactFlow()

  const layout = useMemo(
    () =>
      layoutLineage(
        graph.nodes,
        graph.edges,
        graph.generation_meta.map((entry) => entry.index),
      ),
    [graph],
  )

  // The fill scale is derived from the run itself rather than assumed: the
  // objectives are a discrepancy and a complexity, whose ranges have nothing in
  // common between one problem and the next.
  const range = useMemo(() => {
    const values = graph.nodes
      .filter((node) => node.kind === 'individual')
      .map((node) => node.objectives?.[0])
      .filter((value): value is number => typeof value === 'number')
    if (values.length === 0) return null
    return { min: Math.min(...values), max: Math.max(...values) }
  }, [graph.nodes])

  const rankOf = (objectives: number[] | null | undefined): number => {
    const value = objectives?.[0]
    if (typeof value !== 'number' || !range) return 0
    if (range.max === range.min) return 1
    // Lower is better, so invert: the best candidate gets rank 1.
    return 1 - (value - range.min) / (range.max - range.min)
  }

  // What each operator actually did, so its hover card can show the change
  // rather than just a name.
  const context = useMemo(() => {
    const byId = new Map(graph.nodes.map((node) => [node.id, node]))
    const built = new Map<string, { parentTerms: string[][]; childTerms: string[] | null }>()

    for (const node of graph.nodes) {
      if (node.kind !== 'operator') continue

      const parentTerms = graph.edges
        .filter((edge) => edge.target === node.id)
        .map((edge) => byId.get(edge.source))
        .filter((parent) => parent?.kind === 'individual')
        .map((parent) => parent!.terms)

      // Chained operators hand off through `chain` edges; the produced
      // candidate hangs off the last link.
      let cursor = node.id
      let childTerms: string[] | null = null
      const seen = new Set<string>()
      while (!seen.has(cursor)) {
        seen.add(cursor)
        const onward = graph.edges.find(
          (edge) => edge.source === cursor && (edge.kind === 'produces' || edge.kind === 'chain'),
        )
        if (!onward) break
        const target = byId.get(onward.target)
        if (!target) break
        if (target.kind === 'individual') {
          childTerms = target.terms
          break
        }
        cursor = target.id
      }

      built.set(node.id, { parentTerms, childTerms })
    }
    return built
  }, [graph])

  const flowNodes = useMemo<Node[]>(() => {
    const lanes: Node[] = layout.lanes.map((lane) => {
      const info = graph.generation_meta.find((entry) => entry.index === lane.generation)
      return {
        id: `lane:${lane.generation}`,
        type: 'generationLane',
        position: { x: -LANE_PADDING - LANE_LABEL_GUTTER, y: lane.y },
        width: layout.width + LANE_PADDING * 2 + LANE_LABEL_GUTTER,
        height: lane.height,
        data: {
          label: info?.label ?? `gen ${lane.generation}`,
          isEvolutionary: info?.is_evolutionary ?? true,
          isEmpty: lane.isEmpty,
          emptyReason: graph.only_winning_path
            ? 'no ancestors of the final front in this population'
            : 'nothing recorded for this generation',
        },
        draggable: false,
        selectable: false,
        focusable: false,
        zIndex: 0,
      }
    })

    const elements: Node[] = layout.nodes.map((node) =>
      node.kind === 'individual'
        ? {
            id: node.id,
            type: 'lineageIndividual',
            position: { x: node.x, y: node.y },
            width: node.width,
            height: node.height,
            handles: node.handles,
            zIndex: 1,
            data: {
              uid: node.uid,
              generation: node.generation,
              objectives: node.objectives ?? null,
              objectiveNames: graph.objective_names,
              paretoRank: node.pareto_rank ?? null,
              terms: node.terms,
              isOnFront: node.is_on_front,
              isFinal: node.is_final_choice,
              isCurrentBest: node.is_current_best,
              onWinningPath: node.on_winning_path,
              rank: rankOf(node.objectives),
              selected: node.uid === selectedUid,
            },
          }
        : {
            id: node.id,
            type: 'lineageOperator',
            position: { x: node.x, y: node.y },
            width: node.width,
            height: node.height,
            handles: node.handles,
            zIndex: 1,
            data: {
              operatorType: node.operator_type ?? 'operator',
              label: node.label ?? '',
              onWinningPath: node.on_winning_path,
              parentTerms: context.get(node.id)?.parentTerms ?? [],
              childTerms: context.get(node.id)?.childTerms ?? null,
            },
          },
    )

    return [...lanes, ...elements]
  }, [layout, selectedUid, range, graph.generation_meta, graph.only_winning_path, graph.objective_names, context])

  const flowEdges = useMemo<Edge[]>(
    () =>
      graph.edges.map((edge) => {
        const survival = edge.kind === 'survival'
        const stroke = survival
          ? alpha(theme.palette.text.primary, 0.28)
          : alpha(operatorColor(edge.kind === 'produces' ? null : edge.kind), 0.85)
        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          // Bezier rather than orthogonal: edges from neighbouring sources
          // produce coincident vertical segments that read as one line.
          type: 'default',
          zIndex: 0,
          style: {
            stroke,
            strokeWidth: survival ? 1.1 : 1.6,
            // A carried-over candidate is not a new creation; dashing it keeps
            // the eye on the lines where something happened.
            strokeDasharray: survival ? '3 3' : undefined,
          },
        }
      }),
    [graph.edges, theme],
  )

  const key = useMemo(
    () => `${graph.nodes.length}:${graph.edges.length}:${graph.only_winning_path}`,
    [graph],
  )
  useEffect(() => {
    const timer = window.setTimeout(() => fitView({ padding: 0.12, duration: 240 }), 40)
    return () => window.clearTimeout(timer)
  }, [key, fitView])

  const handleClick: NodeMouseHandler = (_, node) => {
    if (node.type !== 'lineageIndividual') return
    const uid = (node.data as { uid?: string }).uid
    if (uid) onSelect?.(uid)
  }

  if (graph.nodes.length === 0) {
    return (
      <Box sx={{ height: '100%', display: 'grid', placeItems: 'center', px: 4 }}>
        <Typography variant="body2" color="text.disabled" textAlign="center">
          This run has no recorded genealogy — the search never produced a second generation.
        </Typography>
      </Box>
    )
  }

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodeClick={handleClick}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable
      minZoom={0.05}
      maxZoom={2.5}
      proOptions={{ hideAttribution: true }}
      style={{ background: theme.palette.background.default }}
    >
      <Background variant={BackgroundVariant.Dots} gap={20} size={1} color={theme.palette.divider} />
      <Controls showInteractive={false} />
      <MiniMap
        pannable
        zoomable
        nodeColor={(node) =>
          node.type === 'lineageOperator'
            ? operatorColor((node.data as { operatorType?: string }).operatorType)
            : (node.data as { isFinal?: boolean }).isFinal
              ? theme.palette.success.main
              : theme.palette.primary.main
        }
        maskColor={alpha(theme.palette.background.default, 0.72)}
        style={{
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      />
    </ReactFlow>
  )
}

export default function LineageCanvas(props: Props) {
  const [ready, setReady] = useState(false)
  useEffect(() => setReady(true), [])
  if (!ready) return null

  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  )
}

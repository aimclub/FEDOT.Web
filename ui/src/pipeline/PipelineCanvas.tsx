import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Connection,
  type Edge,
  type NodeMouseHandler,
} from '@xyflow/react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'

import type { PipelineGraph } from '../api/types'
import { groupColor } from '../theme'
import PipelineNodeCard, { type PipelineFlowNode } from './PipelineNodeCard'
import { layoutGraph, type LayoutDirection } from './layout'
import { selectVisibleParams } from './paramDisplay'

const nodeTypes = { pipelineNode: PipelineNodeCard }

interface Props {
  graph: PipelineGraph
  direction?: LayoutDirection
  selectedNodeId?: string | null
  problems?: Record<string, string>
  readOnly?: boolean
  onSelect?: (nodeId: string | null) => void
  onConnect?: (source: string, target: string) => void
  onDisconnect?: (source: string, target: string) => void
  emptyHint?: string
}

function Canvas({
  graph,
  direction = 'LR',
  selectedNodeId,
  problems,
  readOnly,
  onSelect,
  onConnect,
  onDisconnect,
  emptyHint,
}: Props) {
  const theme = useTheme()
  const { fitView } = useReactFlow()

  const flowNodes = useMemo<PipelineFlowNode[]>(() => {
    const nodes = graph.nodes.map((node) => {
      const { visible, hidden, total, fromDefaults } = selectVisibleParams(node)
      return {
        id: node.id,
        type: 'pipelineNode' as const,
        position: { x: 0, y: 0 },
        selected: node.id === selectedNodeId,
        data: {
          operation: node.operation,
          group: node.group ?? 'model',
          kind: node.kind ?? 'model',
          description: node.description,
          tags: node.tags ?? [],
          params: node.params ?? {},
          defaults: node.defaults ?? {},
          isPrimary: node.is_primary,
          isRoot: node.is_root,
          visibleParams: visible,
          paramsFromDefaults: fromDefaults,
          // The caption row above default values needs its own line of height.
          paramCount: total + (fromDefaults ? 1 : 0),
          hiddenParamCount: hidden,
          problem: problems?.[node.id] ?? null,
          readOnly,
          horizontal: direction === 'LR',
        },
      }
    })
    return layoutGraph(nodes, graph.edges.map((edge) => ({
      id: edge.id ?? `${edge.source}->${edge.target}`,
      source: edge.source,
      target: edge.target,
    })), direction)
  }, [graph, direction, selectedNodeId, problems, readOnly])

  const flowEdges = useMemo<Edge[]>(
    () =>
      graph.edges.map((edge) => {
        const sourceNode = graph.nodes.find((node) => node.id === edge.source)
        const stroke = groupColor(sourceNode?.group ?? undefined)
        return {
          id: edge.id ?? `${edge.source}->${edge.target}`,
          source: edge.source,
          target: edge.target,
          animated: false,
          style: { stroke: alpha(stroke, 0.75), strokeWidth: 1.8 },
          markerEnd: { type: 'arrowclosed', color: alpha(stroke, 0.75), width: 16, height: 16 } as never,
        }
      }),
    [graph],
  )

  // Re-fit whenever the topology changes, so a newly composed pipeline is
  // fully visible without the user reaching for the zoom controls.
  const topologyKey = useMemo(
    () => `${graph.nodes.map((n) => n.id).join(',')}|${graph.edges.length}|${direction}`,
    [graph, direction],
  )
  useEffect(() => {
    const timer = window.setTimeout(() => fitView({ padding: 0.18, duration: 220 }), 40)
    return () => window.clearTimeout(timer)
  }, [topologyKey, fitView])

  const handleNodeClick = useCallback<NodeMouseHandler>(
    (_, node) => onSelect?.(node.id),
    [onSelect],
  )

  const handleConnect = useCallback(
    (connection: Connection) => {
      if (connection.source && connection.target) {
        onConnect?.(connection.source, connection.target)
      }
    },
    [onConnect],
  )

  const handleEdgesDelete = useCallback(
    (edges: Edge[]) => {
      for (const edge of edges) onDisconnect?.(edge.source, edge.target)
    },
    [onDisconnect],
  )

  if (graph.nodes.length === 0) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'grid',
          placeItems: 'center',
          color: 'text.disabled',
          px: 4,
          textAlign: 'center',
        }}
      >
        <Typography variant="body2">{emptyHint ?? 'This pipeline has no nodes yet.'}</Typography>
      </Box>
    )
  }

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodeClick={handleNodeClick}
      onPaneClick={() => onSelect?.(null)}
      onConnect={handleConnect}
      onEdgesDelete={handleEdgesDelete}
      nodesDraggable={false}
      nodesConnectable={!readOnly}
      elementsSelectable
      edgesFocusable={!readOnly}
      deleteKeyCode={readOnly ? null : ['Backspace', 'Delete']}
      minZoom={0.15}
      maxZoom={2.5}
      proOptions={{ hideAttribution: true }}
      style={{ background: theme.palette.background.default }}
    >
      <Background
        variant={BackgroundVariant.Dots}
        gap={18}
        size={1}
        color={theme.palette.divider}
      />
      <Controls showInteractive={false} />
      <MiniMap
        pannable
        zoomable
        nodeColor={(node) => groupColor((node.data as { group?: string })?.group)}
        maskColor={alpha(theme.palette.background.default, 0.72)}
        style={{
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      />
    </ReactFlow>
  )
}

/** Zoom, pan and a minimap — all of which the previous editor left disabled. */
export default function PipelineCanvas(props: Props) {
  const [ready, setReady] = useState(false)
  useEffect(() => setReady(true), [])
  if (!ready) return null

  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  )
}

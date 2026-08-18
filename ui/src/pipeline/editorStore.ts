import { create } from 'zustand'

import type { GraphEdge, GraphNode, OperationSummary, PipelineGraph, ValidationResult } from '../api/types'

const emptyGraph = (): PipelineGraph => ({ uid: '', nodes: [], edges: [], depth: 0, length: 0 })

let nodeCounter = 0
const nextNodeId = (existing: GraphNode[]): string => {
  // Keep ids unique even after nodes are deleted and the counter is reused.
  const taken = new Set(existing.map((node) => node.id))
  let candidate: string
  do {
    candidate = `n${nodeCounter++}`
  } while (taken.has(candidate))
  return candidate
}

const recomputeRelations = (graph: PipelineGraph): PipelineGraph => {
  const parents = new Map<string, string[]>()
  const children = new Map<string, string[]>()
  for (const node of graph.nodes) {
    parents.set(node.id, [])
    children.set(node.id, [])
  }
  for (const edge of graph.edges) {
    parents.get(edge.target)?.push(edge.source)
    children.get(edge.source)?.push(edge.target)
  }
  return {
    ...graph,
    nodes: graph.nodes.map((node) => ({
      ...node,
      parents: parents.get(node.id) ?? [],
      children: children.get(node.id) ?? [],
      is_primary: (parents.get(node.id) ?? []).length === 0,
      is_root: (children.get(node.id) ?? []).length === 0,
    })),
  }
}

/** Would adding `source -> target` close a cycle? */
const wouldCycle = (edges: GraphEdge[], source: string, target: string): boolean => {
  const adjacency = new Map<string, string[]>()
  for (const edge of edges) {
    const list = adjacency.get(edge.source) ?? []
    list.push(edge.target)
    adjacency.set(edge.source, list)
  }
  const stack = [target]
  const seen = new Set<string>()
  while (stack.length) {
    const current = stack.pop()!
    if (current === source) return true
    if (seen.has(current)) continue
    seen.add(current)
    stack.push(...(adjacency.get(current) ?? []))
  }
  return false
}

interface EditorState {
  graph: PipelineGraph
  task: string | null
  selectedNodeId: string | null
  validation: ValidationResult | null
  dirty: boolean
  name: string
  pipelineUid: string | null

  setGraph: (graph: PipelineGraph, options?: { name?: string; uid?: string | null; clean?: boolean }) => void
  reset: () => void
  setTask: (task: string | null) => void
  setName: (name: string) => void
  setValidation: (validation: ValidationResult | null) => void
  select: (nodeId: string | null) => void

  addOperation: (operation: OperationSummary, defaults: Record<string, unknown>) => string
  removeNode: (nodeId: string) => void
  replaceOperation: (nodeId: string, operation: OperationSummary, defaults: Record<string, unknown>) => void
  setNodeParams: (nodeId: string, params: Record<string, unknown>) => void
  connect: (source: string, target: string) => string | null
  disconnect: (source: string, target: string) => void
}

export const useEditorStore = create<EditorState>((set, get) => ({
  graph: emptyGraph(),
  task: null,
  selectedNodeId: null,
  validation: null,
  dirty: false,
  name: 'Untitled pipeline',
  pipelineUid: null,

  setGraph: (graph, options) =>
    set({
      graph: recomputeRelations(graph),
      selectedNodeId: null,
      validation: null,
      dirty: options?.clean ? false : true,
      ...(options?.name !== undefined ? { name: options.name } : {}),
      ...(options?.uid !== undefined ? { pipelineUid: options.uid } : {}),
    }),

  reset: () =>
    set({
      graph: emptyGraph(),
      selectedNodeId: null,
      validation: null,
      dirty: false,
      name: 'Untitled pipeline',
      pipelineUid: null,
    }),

  setTask: (task) => set({ task, validation: null }),
  setName: (name) => set({ name, dirty: true }),
  setValidation: (validation) => set({ validation }),
  select: (nodeId) => set({ selectedNodeId: nodeId }),

  addOperation: (operation, defaults) => {
    const { graph } = get()
    const id = nextNodeId(graph.nodes)
    const node: GraphNode = {
      id,
      operation: operation.id,
      label: operation.id,
      kind: operation.kind,
      group: operation.group,
      description: operation.description,
      tags: operation.tags,
      params: { ...defaults },
      defaults: { ...defaults },
      parents: [],
      children: [],
      is_primary: true,
      is_root: true,
    }
    set({
      graph: recomputeRelations({ ...graph, nodes: [...graph.nodes, node] }),
      selectedNodeId: id,
      validation: null,
      dirty: true,
    })
    return id
  },

  removeNode: (nodeId) => {
    const { graph, selectedNodeId } = get()
    set({
      graph: recomputeRelations({
        ...graph,
        nodes: graph.nodes.filter((node) => node.id !== nodeId),
        edges: graph.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
      }),
      selectedNodeId: selectedNodeId === nodeId ? null : selectedNodeId,
      validation: null,
      dirty: true,
    })
  },

  replaceOperation: (nodeId, operation, defaults) => {
    const { graph } = get()
    set({
      graph: recomputeRelations({
        ...graph,
        nodes: graph.nodes.map((node) =>
          node.id === nodeId
            ? {
                ...node,
                operation: operation.id,
                label: operation.id,
                kind: operation.kind,
                group: operation.group,
                description: operation.description,
                tags: operation.tags,
                // Parameters belong to the previous operation; start clean.
                params: { ...defaults },
                defaults: { ...defaults },
              }
            : node,
        ),
      }),
      validation: null,
      dirty: true,
    })
  },

  setNodeParams: (nodeId, params) => {
    const { graph } = get()
    set({
      graph: {
        ...graph,
        nodes: graph.nodes.map((node) => (node.id === nodeId ? { ...node, params } : node)),
      },
      validation: null,
      dirty: true,
    })
  },

  connect: (source, target) => {
    const { graph } = get()
    if (source === target) return 'A node cannot be its own parent'
    if (graph.edges.some((edge) => edge.source === source && edge.target === target)) {
      return 'These nodes are already connected'
    }
    if (wouldCycle(graph.edges, source, target)) {
      return 'That connection would create a cycle — pipelines must stay acyclic'
    }
    set({
      graph: recomputeRelations({
        ...graph,
        edges: [...graph.edges, { id: `${source}->${target}`, source, target }],
      }),
      validation: null,
      dirty: true,
    })
    return null
  },

  disconnect: (source, target) => {
    const { graph } = get()
    set({
      graph: recomputeRelations({
        ...graph,
        edges: graph.edges.filter((edge) => !(edge.source === source && edge.target === target)),
      }),
      validation: null,
      dirty: true,
    })
  },
}))

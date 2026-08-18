import type {
  AnalysisKind,
  AnalysisRecord,
  Capabilities,
  DatasetRecord,
  DatasetUploadResult,
  EvolutionControls,
  IndividualPipeline,
  LineageGraph,
  OperationDetail,
  OperationSummary,
  PipelineGraph,
  PipelineRecord,
  PreprocessingReport,
  RunConfig,
  RunControlState,
  RunEvent,
  RunProgress,
  RunRecord,
  ValidationResult,
} from './types'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** Pull a useful message out of FastAPI's error shapes. */
const errorMessage = async (response: Response): Promise<string> => {
  try {
    const body = await response.json()
    const detail = body?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      // Pydantic validation errors: [{loc: [...], msg: "..."}]
      return detail
        .map((item) => {
          const where = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : ''
          return where ? `${where}: ${item?.msg}` : String(item?.msg ?? item)
        })
        .join('; ')
    }
    return JSON.stringify(body)
  } catch {
    return response.statusText || `Request failed with status ${response.status}`
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

const json = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const api = {
  capabilities: () => request<Capabilities>('/capabilities'),

  // ------------------------------------------------------------------ catalog
  operations: (params: { task?: string; kind?: string; includeNonDefault?: boolean } = {}) => {
    const query = new URLSearchParams()
    if (params.task) query.set('task', params.task)
    if (params.kind) query.set('kind', params.kind)
    if (params.includeNonDefault === false) query.set('include_non_default', 'false')
    const suffix = query.toString()
    return request<OperationSummary[]>(`/operations${suffix ? `?${suffix}` : ''}`)
  },
  operation: (id: string) => request<OperationDetail>(`/operations/${encodeURIComponent(id)}`),

  // ---------------------------------------------------------------- pipelines
  pipelines: (runUid?: string) =>
    request<PipelineRecord[]>(`/pipelines${runUid ? `?run_uid=${encodeURIComponent(runUid)}` : ''}`),
  pipeline: (uid: string) => request<PipelineRecord>(`/pipelines/${uid}`),
  savePipeline: (body: { name: string; task?: string | null; graph: PipelineGraph; uid?: string }) =>
    request<PipelineRecord>('/pipelines', json(body)),
  deletePipeline: (uid: string) => request<void>(`/pipelines/${uid}`, { method: 'DELETE' }),
  validatePipeline: (graph: PipelineGraph, task?: string | null) =>
    request<ValidationResult>('/pipelines/validate', json({ graph, task })),
  describePipeline: (graph: PipelineGraph) =>
    request<PipelineGraph>('/pipelines/describe', json(graph)),
  importPipeline: (payload: unknown) => request<PipelineGraph>('/pipelines/import', json(payload)),
  exportPipelineUrl: (uid: string) => `${BASE}/pipelines/${uid}/export`,

  // ----------------------------------------------------------------- datasets
  datasets: () => request<DatasetRecord[]>('/datasets'),
  dataset: (uid: string) => request<DatasetRecord>(`/datasets/${uid}`),
  datasetPreview: (uid: string) =>
    request<{ columns: DatasetRecord['columns']; preview: Record<string, unknown>[]; n_rows: number }>(
      `/datasets/${uid}/preview`,
    ),
  uploadDataset: (file: File, options: { name?: string; task?: string; target?: string } = {}) => {
    const form = new FormData()
    form.append('file', file)
    if (options.name) form.append('name', options.name)
    if (options.task) form.append('task', options.task)
    if (options.target) form.append('target', options.target)
    return request<DatasetUploadResult>('/datasets', { method: 'POST', body: form })
  },
  updateDataset: (uid: string, changes: { target?: string; task?: string }) => {
    const form = new FormData()
    if (changes.target) form.append('target', changes.target)
    if (changes.task) form.append('task', changes.task)
    return request<DatasetRecord>(`/datasets/${uid}`, { method: 'PATCH', body: form })
  },
  deleteDataset: (uid: string) => request<void>(`/datasets/${uid}`, { method: 'DELETE' }),

  // --------------------------------------------------------------------- runs
  runs: () => request<RunRecord[]>('/runs'),
  run: (uid: string) => request<RunRecord>(`/runs/${uid}`),
  startRun: (config: RunConfig, name?: string) =>
    request<RunRecord>('/runs', json({ name, config })),
  runProgress: (uid: string) => request<RunProgress>(`/runs/${uid}/progress`),
  runEvents: (uid: string, afterId = 0) =>
    request<RunEvent[]>(`/runs/${uid}/events?after_id=${afterId}`),
  stopRun: (uid: string) => request<RunRecord>(`/runs/${uid}/stop`, { method: 'POST' }),
  /** Direct link to the saved OptHistory JSON, served as an attachment. */
  historyUrl: (uid: string) => `${BASE}/runs/${uid}/history`,
  deleteRun: (uid: string) => request<void>(`/runs/${uid}`, { method: 'DELETE' }),

  // ----------------------------------------------------------------- controls
  controls: (uid: string) => request<RunControlState>(`/runs/${uid}/controls`),
  setControls: (uid: string, patch: Partial<EvolutionControls>) =>
    request<RunControlState>(`/runs/${uid}/controls`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),

  // ----------------------------------------------------------------- analyses
  analyses: (runUid: string) => request<AnalysisRecord[]>(`/runs/${runUid}/analyses`),
  analysis: (uid: string) => request<AnalysisRecord>(`/analyses/${uid}`),
  startAnalysis: (
    runUid: string,
    body: { kind: AnalysisKind; pipeline_uid?: string; individual_uid?: string; replacements?: number },
  ) => request<AnalysisRecord>(`/runs/${runUid}/analyses`, json(body)),
  /** Analyse a pipeline that belongs to no run, e.g. one drawn in the editor. */
  startStandaloneAnalysis: (body: {
    kind: AnalysisKind
    graph: PipelineGraph
    dataset_uid: string
    target?: string | null
    problem?: string | null
    replacements?: number
  }) => request<AnalysisRecord>('/analyses', json(body)),

  preprocessing: (datasetUid: string, params: { task?: string; target?: string } = {}) => {
    const query = new URLSearchParams()
    if (params.task) query.set('task', params.task)
    if (params.target) query.set('target', params.target)
    const suffix = query.toString()
    return request<PreprocessingReport>(
      `/datasets/${datasetUid}/preprocessing${suffix ? `?${suffix}` : ''}`,
    )
  },

  // ------------------------------------------------------------------ lineage
  lineage: (uid: string, full = false) =>
    request<LineageGraph>(`/runs/${uid}/lineage${full ? '?full=true' : ''}`),
  lineagePipeline: (uid: string, individualUid: string) =>
    request<IndividualPipeline>(`/runs/${uid}/lineage/${individualUid}`),
}

/** Open the progress socket for a run; the caller owns closing it. */
export const openRunStream = (uid: string): WebSocket => {
  const base = new URL(BASE, window.location.href)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  base.pathname = `${base.pathname.replace(/\/$/, '')}/runs/${uid}/stream`
  return new WebSocket(base.toString())
}

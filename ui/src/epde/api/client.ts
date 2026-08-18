/**
 * HTTP client for the EPDE module.
 *
 * Deliberately standalone rather than an extension of `src/api/client.ts`: the
 * module is meant to be liftable into its own application, and the shared part
 * is forty lines of `fetch` wrapper. What is *not* duplicated is the base path
 * — everything here hangs off `/api/epde`, which is where FEDOT.Web mounts the
 * module and where a standalone EPDE.Web would serve it from as `/api`.
 */

import type {
  DatasetPreview,
  DatasetRecord,
  EpdeCapabilities,
  EpdeRunConfig,
  EpdeRunRecord,
  EvolutionControls,
  LineageGraph,
  RunControlState,
  RunEvent,
  RunProgress,
  RunResult,
  SystemGraph,
  SystemRecord,
} from './types'

const BASE = import.meta.env.VITE_EPDE_API_BASE ?? '/api/epde'

export class EpdeApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'EpdeApiError'
  }
}

/** Pull a useful message out of FastAPI's error shapes. */
const errorMessage = async (response: Response): Promise<string> => {
  try {
    const body = await response.json()
    const detail = body?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
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
    throw new EpdeApiError(response.status, await errorMessage(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

const json = (body: unknown): RequestInit => ({ method: 'POST', body: JSON.stringify(body) })

export const epdeApi = {
  capabilities: () => request<EpdeCapabilities>('/capabilities'),

  // ----------------------------------------------------------------- datasets
  datasets: () => request<DatasetRecord[]>('/datasets'),
  dataset: (uid: string) => request<DatasetRecord>(`/datasets/${uid}`),
  uploadDataset: (file: File, name?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (name) form.append('name', name)
    return request<DatasetRecord>('/datasets', { method: 'POST', body: form })
  },
  createSample: (sampleId: string) =>
    request<DatasetRecord>(`/datasets/samples/${sampleId}`, { method: 'POST' }),
  updateAxes: (uid: string, axes: { name?: string; start?: number; stop?: number }[]) =>
    request<DatasetRecord>(`/datasets/${uid}/axes`, {
      method: 'PATCH',
      body: JSON.stringify({ axes }),
    }),
  preview: (uid: string, sliceAt?: number[]) => {
    const query = (sliceAt ?? []).map((value) => `slice_at=${value}`).join('&')
    return request<DatasetPreview>(`/datasets/${uid}/preview${query ? `?${query}` : ''}`)
  },
  datasetExportUrl: (uid: string) => `${BASE}/datasets/${uid}/export`,
  deleteDataset: (uid: string) => request<void>(`/datasets/${uid}`, { method: 'DELETE' }),

  // --------------------------------------------------------------------- runs
  runs: () => request<EpdeRunRecord[]>('/runs'),
  run: (uid: string) => request<EpdeRunRecord>(`/runs/${uid}`),
  startRun: (config: EpdeRunConfig, name?: string) =>
    request<EpdeRunRecord>('/runs', json({ name, config })),
  progress: (uid: string) => request<RunProgress>(`/runs/${uid}/progress`),
  result: (uid: string) => request<RunResult>(`/runs/${uid}/result`),
  events: (uid: string, afterId = 0) =>
    request<RunEvent[]>(`/runs/${uid}/events?after_id=${afterId}`),
  stopRun: (uid: string) => request<EpdeRunRecord>(`/runs/${uid}/stop`, { method: 'POST' }),
  deleteRun: (uid: string) => request<void>(`/runs/${uid}`, { method: 'DELETE' }),
  /** The module's own saved history; EPDE keeps nothing after a search. */
  historyUrl: (uid: string) => `${BASE}/runs/${uid}/history`,

  // ----------------------------------------------------------------- controls
  controls: (uid: string) => request<RunControlState>(`/runs/${uid}/controls`),
  setControls: (uid: string, patch: Partial<EvolutionControls>) =>
    request<RunControlState>(`/runs/${uid}/controls`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),

  // ------------------------------------------------------------------ lineage
  lineage: (uid: string, full = false) =>
    request<LineageGraph>(`/runs/${uid}/lineage${full ? '?full=true' : ''}`),
  lineageSystem: (uid: string, individualUid: string) =>
    request<SystemGraph>(`/runs/${uid}/lineage/${individualUid}`),

  // ------------------------------------------------------------------ systems
  systems: (runUid?: string) =>
    request<SystemRecord[]>(`/systems${runUid ? `?run_uid=${encodeURIComponent(runUid)}` : ''}`),
  saveSystem: (graph: SystemGraph, name: string, runUid?: string) => {
    const query = new URLSearchParams({ name })
    if (runUid) query.set('run_uid', runUid)
    return request<SystemRecord>(`/systems?${query.toString()}`, json(graph))
  },
  deleteSystem: (uid: string) => request<void>(`/systems/${uid}`, { method: 'DELETE' }),
}

/** Open the progress socket for a run; the caller owns closing it. */
export const openEpdeRunStream = (uid: string): WebSocket => {
  const base = new URL(BASE, window.location.href)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  base.pathname = `${base.pathname.replace(/\/$/, '')}/runs/${uid}/stream`
  return new WebSocket(base.toString())
}

import { useCallback, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../api/client'
import type { AnalysisKind, AnalysisRecord, PipelineGraph } from '../api/types'

/**
 * Start an analysis and follow it to completion.
 *
 * Both kinds refit the pipeline many times, so they run out of process and are
 * polled for rather than awaited.
 */
export function useAnalysis(runUid: string, kind: AnalysisKind) {
  const queryClient = useQueryClient()
  const [uid, setUid] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  const { data: record } = useQuery<AnalysisRecord>({
    queryKey: ['analysis', uid],
    queryFn: () => api.analysis(uid!),
    enabled: Boolean(uid),
    refetchInterval: (query) => (query.state.data?.status === 'running' ? 2000 : false),
  })

  // The most recent finished analysis of this kind, so reopening the window does
  // not mean paying for the computation again.
  const { data: previous } = useQuery({
    queryKey: ['analyses', runUid],
    queryFn: () => api.analyses(runUid),
    select: (all) => all.find((item) => item.kind === kind && item.status === 'finished') ?? null,
    // The panel can be mounted without a run (editor mode); nothing to list then.
    enabled: Boolean(runUid),
  })

  const start = useCallback(
    async (options: { replacements?: number; individual_uid?: string } = {}) => {
      setStarting(true)
      setStartError(null)
      try {
        const started = await api.startAnalysis(runUid, { kind, ...options })
        setUid(started.uid)
        void queryClient.invalidateQueries({ queryKey: ['analyses', runUid] })
      } catch (error) {
        setStartError((error as Error).message)
      } finally {
        setStarting(false)
      }
    },
    [runUid, kind, queryClient],
  )

  const current = record ?? (uid ? null : previous)

  return {
    start,
    starting,
    startError,
    record: current,
    isRunning: starting || current?.status === 'running',
    /** True when what is shown came from an earlier request, not this one. */
    isCached: !uid && Boolean(previous),
  }
}

/**
 * The editor's variant: the pipeline belongs to no run, so the caller names the
 * dataset to fit it on. No cache of earlier results - a drawn pipeline has no
 * identity to look one up by.
 */
export function useStandaloneAnalysis(kind: AnalysisKind) {
  const [uid, setUid] = useState<string | null>(null)
  const [startError, setStartError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)

  const { data: record } = useQuery<AnalysisRecord>({
    queryKey: ['analysis', uid],
    queryFn: () => api.analysis(uid!),
    enabled: Boolean(uid),
    refetchInterval: (query) => (query.state.data?.status === 'running' ? 2000 : false),
  })

  const start = useCallback(
    async (body: {
      graph: PipelineGraph
      dataset_uid: string
      target?: string | null
      problem?: string | null
      replacements?: number
    }) => {
      setStarting(true)
      setStartError(null)
      try {
        const started = await api.startStandaloneAnalysis({ kind, ...body })
        setUid(started.uid)
      } catch (error) {
        setStartError((error as Error).message)
      } finally {
        setStarting(false)
      }
    },
    [kind],
  )

  return {
    start,
    starting,
    startError,
    record: record ?? null,
    isRunning: starting || record?.status === 'running',
    isCached: false,
  }
}

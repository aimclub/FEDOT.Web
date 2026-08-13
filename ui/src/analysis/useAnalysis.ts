import { useCallback, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '../api/client'
import type { AnalysisKind, AnalysisRecord } from '../api/types'

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

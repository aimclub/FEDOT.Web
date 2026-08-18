import { useEffect, useRef, useState } from 'react'

import { openRunStream } from '../api/client'
import type { GenerationPoint, PipelineGraph, RunEvent } from '../api/types'

export interface RunStreamState {
  connected: boolean
  generations: GenerationPoint[]
  bestPipeline: PipelineGraph | null
  logs: { message: string; level: string; elapsed?: number | null }[]
  status: string | null
  elapsed: number | null
}

const EMPTY: RunStreamState = {
  connected: false,
  generations: [],
  bestPipeline: null,
  logs: [],
  status: null,
  elapsed: null,
}

/**
 * Follow a run's progress over a WebSocket.
 *
 * The server replays every stored event on connect, so the hook rebuilds the
 * full fitness curve from scratch — a reload or a late-opened tab shows the same
 * picture as one that watched from the start.
 */
export function useRunStream(uid: string | undefined, enabled: boolean): RunStreamState {
  const [state, setState] = useState<RunStreamState>(EMPTY)
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!uid || !enabled) {
      setState(EMPTY)
      return
    }

    setState(EMPTY)
    let closed = false
    const socket = openRunStream(uid)
    socketRef.current = socket

    socket.onopen = () => {
      if (!closed) setState((current) => ({ ...current, connected: true }))
    }

    socket.onmessage = (message) => {
      let event: RunEvent
      try {
        event = JSON.parse(message.data as string)
      } catch {
        return
      }
      if (event.kind === 'ping') return

      setState((current) => {
        const payload = event.payload ?? {}
        switch (event.kind) {
          case 'generation': {
            const point: GenerationPoint = {
              generation: Number(payload.generation ?? current.generations.length),
              size: Number(payload.size ?? 0),
              best_fitness: (payload.best_fitness as number | undefined) ?? null,
              mean_fitness: (payload.mean_fitness as number | undefined) ?? null,
              worst_fitness: (payload.worst_fitness as number | undefined) ?? null,
              elapsed: event.elapsed ?? null,
              best_uid:
                ((payload.best_pipeline as { uid?: string } | null)?.uid ?? null) || null,
              best_operations: (
                (payload.best_pipeline as { nodes?: { operation?: string }[] } | null)?.nodes ?? []
              ).map((node) => String(node.operation ?? '')),
            }
            // Replays can repeat a generation; keep one entry per index.
            const generations = current.generations.filter(
              (existing) => existing.generation !== point.generation,
            )
            generations.push(point)
            generations.sort((a, b) => a.generation - b.generation)

            return {
              ...current,
              generations,
              elapsed: event.elapsed ?? current.elapsed,
              bestPipeline: (payload.best_pipeline as PipelineGraph | null) ?? current.bestPipeline,
            }
          }
          case 'status':
          case 'run_status':
            return { ...current, status: String(payload.status ?? current.status) }
          case 'log':
            return {
              ...current,
              logs: [
                ...current.logs.slice(-199),
                {
                  message: String(payload.message ?? ''),
                  level: String(payload.level ?? 'info'),
                  elapsed: event.elapsed ?? null,
                },
              ],
            }
          case 'error':
            return {
              ...current,
              status: 'failed',
              logs: [
                ...current.logs.slice(-199),
                { message: String(payload.message ?? 'Run failed'), level: 'error' },
              ],
            }
          case 'finished':
            return { ...current, status: 'finished' }
          case 'cancelled':
            return { ...current, status: 'cancelled' }
          default:
            return current
        }
      })
    }

    const markDisconnected = () => {
      if (!closed) setState((current) => ({ ...current, connected: false }))
    }
    socket.onclose = markDisconnected
    socket.onerror = markDisconnected

    return () => {
      closed = true
      socketRef.current = null
      // Only close a socket that finished opening; closing during CONNECTING
      // produces a console error in some browsers.
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CLOSING) {
        socket.close()
      } else {
        socket.addEventListener('open', () => socket.close(), { once: true })
      }
    }
  }, [uid, enabled])

  return state
}

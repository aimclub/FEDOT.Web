import { useEffect, useRef, useState } from 'react'

import { openEpdeRunStream } from '../api/client'
import type { GenerationPoint, RunEvent, SystemGraph } from '../api/types'

/**
 * Live progress for one run.
 *
 * The socket carries everything except the population events: those hold every
 * candidate system in a generation and belong to the genealogy view, which
 * fetches them when it is open. A socket that pushed them would spend most of
 * its bandwidth on a panel that may not even be on screen.
 */

export interface StreamState {
  connected: boolean
  status: string | null
  generations: GenerationPoint[]
  best: SystemGraph | null
  objectiveNames: string[]
  logs: { level: string; message: string; elapsed?: number | null }[]
  /** Bumped on every generation, so dependent queries know to refetch. */
  revision: number
  /** What the evaluator is doing inside the current generation. */
  progress: { generation: number; sector: number; sectors: number } | null
  /** Set once the run reaches a terminal state, so the caller can refetch. */
  terminal: boolean
}

const INITIAL: StreamState = {
  connected: false,
  status: null,
  generations: [],
  best: null,
  objectiveNames: [],
  logs: [],
  revision: 0,
  progress: null,
  terminal: false,
}

export function useEpdeRunStream(uid: string | undefined, enabled: boolean): StreamState {
  const [state, setState] = useState<StreamState>(INITIAL)
  const socketRef = useRef<WebSocket | null>(null)
  // The server replays a run's whole event log to every new connection, so a
  // reconnect would otherwise append the same log lines again. Tracking the
  // highest id seen makes replay idempotent, which is what a reconnect during
  // a long generation needs it to be.
  const seenRef = useRef(0)

  useEffect(() => {
    if (!uid || !enabled) return

    let closed = false
    let retry: number | undefined
    seenRef.current = 0
    setState(INITIAL)

    const connect = () => {
      if (closed) return
      const socket = openEpdeRunStream(uid)
      socketRef.current = socket

      socket.onopen = () => setState((current) => ({ ...current, connected: true }))
      socket.onclose = () => {
        setState((current) => ({ ...current, connected: false }))
        // The server keeps a finished run's socket open but quiet; reconnecting
        // after a drop is what keeps a long run watchable through a sleep or a
        // proxy timeout.
        if (!closed) retry = window.setTimeout(connect, 2000)
      }
      socket.onerror = () => socket.close()
      socket.onmessage = (message) => {
        let event: RunEvent
        try {
          event = JSON.parse(message.data)
        } catch {
          return
        }
        if (typeof event.id === 'number') {
          if (event.id <= seenRef.current) return
          seenRef.current = event.id
        }
        setState((current) => reduce(current, event))
      }
    }

    connect()
    return () => {
      closed = true
      if (retry) window.clearTimeout(retry)
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [uid, enabled])

  return state
}

function reduce(state: StreamState, event: RunEvent): StreamState {
  const payload = event.payload ?? {}

  switch (event.kind) {
    case 'generation': {
      const point: GenerationPoint = {
        generation: Number(payload.generation ?? state.generations.length),
        label: String(payload.label ?? ''),
        size: Number(payload.size ?? 0),
        evaluated: Number(payload.evaluated ?? 0),
        front_size: Number(payload.front_size ?? 0),
        objectives: (payload.objectives as GenerationPoint['objectives']) ?? [],
        hypervolume: (payload.hypervolume as number | null) ?? null,
        elapsed: (payload.elapsed as number | null) ?? null,
      }
      // A generation can be re-sent after a reconnect; the newest wins.
      const generations = state.generations.filter(
        (existing) => existing.generation !== point.generation,
      )
      generations.push(point)
      generations.sort((left, right) => left.generation - right.generation)

      return {
        ...state,
        generations,
        best: (payload.best as SystemGraph) ?? state.best,
        objectiveNames: (payload.objective_names as string[]) ?? state.objectiveNames,
        revision: state.revision + 1,
        progress: null,
      }
    }
    case 'progress':
      return {
        ...state,
        progress: {
          generation: Number(payload.generation ?? 0),
          sector: Number(payload.sector ?? 0),
          sectors: Number(payload.sectors ?? 0),
        },
      }
    case 'status':
      return { ...state, status: String(payload.status ?? '') }
    case 'run_status': {
      const status = String(payload.status ?? state.status ?? '')
      return {
        ...state,
        status,
        terminal: ['finished', 'failed', 'cancelled'].includes(status),
      }
    }
    case 'log':
      return {
        ...state,
        logs: [
          ...state.logs.slice(-200),
          {
            level: String(payload.level ?? 'info'),
            message: String(payload.message ?? ''),
            elapsed: event.elapsed ?? null,
          },
        ],
      }
    case 'error':
      return {
        ...state,
        logs: [
          ...state.logs.slice(-200),
          { level: 'error', message: String(payload.message ?? 'The run failed'), elapsed: event.elapsed },
        ],
      }
    case 'finished':
      return {
        ...state,
        best: (payload.best as SystemGraph) ?? state.best,
        objectiveNames: (payload.objective_names as string[]) ?? state.objectiveNames,
        revision: state.revision + 1,
        progress: null,
        terminal: true,
      }
    case 'cancelled':
      return { ...state, terminal: true }
    default:
      return state
  }
}

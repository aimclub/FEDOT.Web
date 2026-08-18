import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import FormControlLabel from '@mui/material/FormControlLabel'
import IconButton from '@mui/material/IconButton'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'

import { EpdeApiError, epdeApi } from '../api/client'
import EquationView from '../equations/EquationView'
import TermTable from '../equations/TermTable'
import LineageCanvas from './LineageCanvas'
import { OPERATOR_COLORS } from './LineageNodes'

/**
 * The evolution history, drawn as a genealogy.
 *
 * The objective curves say the search improved. This says how: which candidate
 * was crossed or mutated into which, and which of those lines reached the final
 * Pareto front. EPDE records none of it — it keeps only the current population
 * and forgets even that when the process ends — so the graph is assembled from
 * what the module observed while the search ran.
 */

function Legend({ isLive }: { isLive: boolean }) {
  const theme = useTheme()
  const items = [
    {
      color: theme.palette.success.main,
      label: isLive ? 'leading front' : 'final front',
      hint: isLive
        ? 'The non-dominated candidates at this point in the run'
        : 'The non-dominated candidates the search returned',
    },
    {
      color: theme.palette.primary.main,
      label: 'ancestor',
      hint: 'On a line of descent to the front',
    },
    { color: OPERATOR_COLORS.mutation, label: 'mutation', hint: 'Changed one candidate into another' },
    { color: OPERATOR_COLORS.crossover, label: 'crossover', hint: 'Combined two parents' },
  ]

  return (
    <Stack direction="row" spacing={1.25} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
      {items.map((item) => (
        <Tooltip key={item.label} title={item.hint}>
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Box
              sx={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                bgcolor: alpha(item.color, 0.3),
                border: '1.5px solid',
                borderColor: item.color,
              }}
            />
            <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>{item.label}</Typography>
          </Stack>
        </Tooltip>
      ))}
      <Tooltip title="The same candidate carried unchanged into the next generation">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box sx={{ width: 16, borderTop: '1.5px dashed', borderColor: 'text.disabled' }} />
          <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>survived</Typography>
        </Stack>
      </Tooltip>
    </Stack>
  )
}

interface Props {
  runUid: string
  isLive?: boolean
  /** Bumped by the caller when a generation arrives, which triggers a refetch. */
  liveRevision?: number
}

export default function EvolutionHistory({ runUid, isLive = false, liveRevision = 0 }: Props) {
  const [showAll, setShowAll] = useState(false)
  const [selectedUid, setSelectedUid] = useState<string | null>(null)
  const [highlightTerm, setHighlightTerm] = useState<string | null>(null)

  const {
    data: lineage,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['epde-lineage', runUid, showAll],
    queryFn: () => epdeApi.lineage(runUid, showAll),
    // A finished run's genealogy never changes; a live one changes every
    // generation and is refreshed by the effect below.
    staleTime: isLive ? 0 : Infinity,
    retry: false,
  })

  useEffect(() => {
    if (isLive) void refetch()
  }, [isLive, liveRevision, refetch])

  const { data: system, isFetching: systemLoading } = useQuery({
    queryKey: ['epde-lineage-system', runUid, selectedUid, isLive ? liveRevision : 0],
    queryFn: () => epdeApi.lineageSystem(runUid, selectedUid!),
    enabled: Boolean(selectedUid),
    staleTime: isLive ? 0 : Infinity,
    // Keep the previous system on screen while the next loads, so the panel
    // does not blink on every generation.
    placeholderData: (previous) => previous,
  })

  if (isLoading) {
    return (
      <Stack alignItems="center" spacing={1.5} sx={{ py: 6 }}>
        <CircularProgress size={24} />
        {isLive && (
          <Typography variant="caption" color="text.secondary">
            Waiting for the first generation…
          </Typography>
        )}
      </Stack>
    )
  }

  if (error) {
    const notFound = error instanceof EpdeApiError && error.status === 404
    return (
      <Alert severity={notFound ? 'info' : 'error'} sx={{ m: 2 }}>
        {notFound
          ? isLive
            ? 'No generation has been reported yet. The genealogy appears once the first population is evaluated.'
            : 'This run recorded no history. It failed before the first population was placed.'
          : (error as Error).message}
      </Alert>
    )
  }

  if (!lineage) return null

  const individuals = lineage.nodes.filter((node) => node.kind === 'individual').length
  const operators = lineage.nodes.filter((node) => node.kind === 'operator').length

  return (
    <Stack sx={{ height: '100%', minHeight: 0 }}>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1.5}
        sx={{
          px: 2,
          py: 1.25,
          borderBottom: '1px solid',
          borderColor: 'divider',
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Tooltip title="The seed population is reported as a row of its own and is not counted here — it is what the search started from, not a round of evolution.">
          <Chip size="small" variant="outlined" label={`${lineage.evolution_generations} generations`} />
        </Tooltip>
        <Chip size="small" variant="outlined" label={`${individuals} candidates`} />
        <Chip size="small" variant="outlined" label={`${operators} operators`} />
        {lineage.hidden_plateau_generations > 0 && (
          <Tooltip title="Generations after the front last changed are not drawn — they only repeat the same candidates. Switch on 'Whole population' to see them.">
            <Chip
              size="small"
              variant="outlined"
              label={`+${lineage.hidden_plateau_generations} unchanged hidden`}
            />
          </Tooltip>
        )}
        {lineage.is_live && (
          <Tooltip title="Assembled from the run's progress events; it grows with each generation.">
            <Chip size="small" color="info" label="updating" />
          </Tooltip>
        )}

        <Divider orientation="vertical" flexItem />
        <Legend isLive={lineage.is_live} />

        <Box sx={{ flexGrow: 1 }} />

        <FormControlLabel
          control={
            <Switch size="small" checked={showAll} onChange={(event) => setShowAll(event.target.checked)} />
          }
          label={
            <Tooltip title="Include every candidate evaluated, not only the ancestors of the front.">
              <Typography variant="body2">Whole population</Typography>
            </Tooltip>
          }
        />

        <Tooltip
          title={
            lineage.is_live
              ? 'The history file is written when the run finishes'
              : 'Download the recorded history. EPDE keeps nothing of its own, so this is the only copy.'
          }
        >
          <span>
            <IconButton
              size="small"
              component="a"
              href={epdeApi.historyUrl(runUid)}
              download={`epde_history_${runUid}.json`}
              disabled={lineage.is_live}
            >
              <DownloadRoundedIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      </Stack>

      {lineage.truncated && (
        <Alert severity="warning" square sx={{ borderRadius: 0, py: 0.3 }}>
          The genealogy was truncated: this run evaluated more candidates than the graph can show.
          The ancestry of the front is complete; the rest is partial.
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexGrow: 1, minHeight: 0 }}>
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <LineageCanvas
            graph={lineage}
            selectedUid={selectedUid}
            onSelect={(uid) => {
              setSelectedUid(uid)
              setHighlightTerm(null)
            }}
          />
        </Box>

        {selectedUid && (
          <Box
            sx={{
              width: 440,
              flexShrink: 0,
              borderLeft: '1px solid',
              borderColor: 'divider',
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}
          >
            <Stack
              direction="row"
              alignItems="center"
              spacing={1}
              sx={{ px: 1.5, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography variant="subtitle2">Candidate {selectedUid}</Typography>
                {system && (
                  <Typography variant="caption" color="text.secondary">
                    generation {system.generation ?? '—'} · {system.active_terms} active terms
                  </Typography>
                )}
              </Box>
              <Box sx={{ flexGrow: 1 }} />
              <Button size="small" onClick={() => setSelectedUid(null)}>
                Close
              </Button>
            </Stack>

            {systemLoading && !system && (
              <Stack alignItems="center" sx={{ py: 4 }}>
                <CircularProgress size={20} />
              </Stack>
            )}

            {system && (
              <Box sx={{ overflowY: 'auto', p: 1.5 }}>
                <EquationView system={system} highlightTermId={highlightTerm} />

                {system.objectives && (
                  <Stack direction="row" spacing={1} sx={{ mt: 1.5, flexWrap: 'wrap' }} useFlexGap>
                    {system.objectives.map((value, index) => (
                      <Chip
                        key={index}
                        size="small"
                        variant="outlined"
                        label={`${system.objective_names?.[index] ?? `objective ${index}`}: ${Number(
                          value.toPrecision(4),
                        )}`}
                      />
                    ))}
                  </Stack>
                )}

                <Divider sx={{ my: 1.5 }} />

                {system.equations.map((equation) => (
                  <Box key={equation.variable} sx={{ mb: 1.5 }}>
                    {system.equations.length > 1 && (
                      <Typography variant="caption" color="text.secondary">
                        {equation.variable}
                      </Typography>
                    )}
                    <TermTable equation={equation} onHighlight={setHighlightTerm} />
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Stack>
  )
}

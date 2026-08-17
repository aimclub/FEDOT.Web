import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import FormControlLabel from '@mui/material/FormControlLabel'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import EditRoundedIcon from '@mui/icons-material/EditRounded'

import { ApiError, api } from '../api/client'
import NodeInspector from '../pipeline/NodeInspector'
import PipelineCanvas from '../pipeline/PipelineCanvas'
import LineageCanvas from './LineageCanvas'
import { OPERATOR_COLORS } from './LineageNodes'

interface Props {
  runUid: string
  /** True while the composition is still going; the graph then updates live. */
  isLive?: boolean
  /**
   * Bumped by the caller whenever a new generation arrives over the socket. The
   * graph refetches on change, which is what keeps it in step with the run.
   */
  liveRevision?: number
  /** Called when the user wants to keep an individual's pipeline. */
  onOpenInEditor?: (uid: string) => void
}

function Legend({ isLive }: { isLive: boolean }) {
  const theme = useTheme()
  const items: { color: string; label: string; hint: string }[] = [
    isLive
      ? {
          color: theme.palette.success.main,
          label: 'best so far',
          hint: 'The leading pipeline at this point in the run',
        }
      : {
          color: theme.palette.success.main,
          label: 'final choice',
          hint: 'The pipeline the run returned',
        },
    {
      color: theme.palette.primary.main,
      label: 'ancestor',
      hint: isLive ? 'On the line of descent to the leader' : 'On the line of descent to the winner',
    },
    { color: OPERATOR_COLORS.mutation, label: 'mutation', hint: 'Changed one pipeline into another' },
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
      <Tooltip title="The same pipeline carried unchanged into the next generation">
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <Box
            sx={{
              width: 16,
              borderTop: '1.5px dashed',
              borderColor: 'text.disabled',
            }}
          />
          <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>survived</Typography>
        </Stack>
      </Tooltip>
    </Stack>
  )
}

/**
 * The evolution history, drawn as a genealogy.
 *
 * The fitness curve on the results screen shows that the population improved.
 * This shows how: which pipelines were crossed or mutated into which, and which
 * of those lines survived to become the returned model.
 */
export default function EvolutionHistory({
  runUid,
  isLive = false,
  liveRevision = 0,
  onOpenInEditor,
}: Props) {
  const [showAll, setShowAll] = useState(false)
  const [selectedUid, setSelectedUid] = useState<string | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const {
    data: lineage,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['lineage', runUid, showAll],
    queryFn: () => api.lineage(runUid, showAll),
    // A finished run's genealogy never changes; a live one changes every
    // generation and is refreshed by the effect below.
    staleTime: isLive ? 0 : Infinity,
    retry: false,
  })

  useEffect(() => {
    if (isLive) void refetch()
  }, [isLive, liveRevision, refetch])

  const { data: pipeline, isFetching: pipelineLoading } = useQuery({
    queryKey: ['lineage-pipeline', runUid, selectedUid, isLive ? liveRevision : 0],
    queryFn: () => api.lineagePipeline(runUid, selectedUid!),
    enabled: Boolean(selectedUid),
    staleTime: isLive ? 0 : Infinity,
    // Keep the previous pipeline on screen while the next one loads, so the
    // panel does not blink on every generation.
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
    const notFound = error instanceof ApiError && error.status === 404
    return (
      <Alert severity={notFound ? 'info' : 'error'} sx={{ m: 2 }}>
        {notFound
          ? isLive
            ? 'No generation has been reported yet. The genealogy appears once the composer evaluates its first population.'
            : 'This run saved no optimisation history. FEDOT skips evolution when the time budget is too small for a generation.'
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
        sx={{ px: 2, py: 1.25, borderBottom: '1px solid', borderColor: 'divider', flexWrap: 'wrap', gap: 1 }}
      >
        <Tooltip title="GOLEM also stores the seed populations and the final choice; those rows are labelled separately and are not counted here.">
          <Chip
            size="small"
            variant="outlined"
            label={`${lineage.evolution_generations} generations`}
          />
        </Tooltip>
        <Chip size="small" variant="outlined" label={`${individuals} pipelines`} />
        <Chip size="small" variant="outlined" label={`${operators} operators`} />
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
            <Tooltip
              title={
                lineage.is_live
                  ? 'Include every pipeline evaluated so far, not only the ancestors of the current leader.'
                  : 'Include every pipeline evaluated, not only the ancestors of the winner. Large runs can reach thousands of nodes.'
              }
            >
              <Typography variant="body2">Whole population</Typography>
            </Tooltip>
          }
        />
      </Stack>

      {lineage.truncated && (
        <Alert severity="warning" square sx={{ borderRadius: 0, py: 0.3 }}>
          The genealogy was truncated because this run evaluated more pipelines than the graph can
          show. The ancestry of the winner is complete; the rest is partial.
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexGrow: 1, minHeight: 0 }}>
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <LineageCanvas
            graph={lineage}
            selectedUid={selectedUid}
            onSelectIndividual={(uid, nodeId) => {
              setSelectedUid(uid)
              setSelectedNodeId(null)
              void nodeId
            }}
          />
        </Box>

        {selectedUid && (
          <Box
            sx={{
              width: 420,
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
                <Typography variant="subtitle2">Selected pipeline</Typography>
                {pipeline && (
                  <Typography variant="caption" color="text.secondary">
                    generation {pipeline.generation} · fitness{' '}
                    {pipeline.fitness === null ? '—' : Number(pipeline.fitness.toFixed(4))}
                  </Typography>
                )}
              </Box>
              <Box sx={{ flexGrow: 1 }} />
              {pipeline && onOpenInEditor && (
                <Tooltip title="Copy this pipeline into the editor">
                  <Button size="small" startIcon={<EditRoundedIcon />} onClick={() => onOpenInEditor(selectedUid)}>
                    Edit
                  </Button>
                </Tooltip>
              )}
              <Button size="small" onClick={() => setSelectedUid(null)}>
                Close
              </Button>
            </Stack>

            {pipelineLoading && !pipeline && (
              <Stack alignItems="center" sx={{ py: 4 }}>
                <CircularProgress size={20} />
              </Stack>
            )}

            {pipeline && (
              <>
                <Box sx={{ height: 240, borderBottom: '1px solid', borderColor: 'divider' }}>
                  <PipelineCanvas
                    graph={pipeline}
                    readOnly
                    selectedNodeId={selectedNodeId}
                    onSelect={setSelectedNodeId}
                  />
                </Box>
                <Box sx={{ flexGrow: 1, minHeight: 0 }}>
                  {selectedNodeId ? (
                    <NodeInspector
                      node={pipeline.nodes.find((node) => node.id === selectedNodeId)!}
                      onParamsChange={() => {}}
                      onDelete={() => {}}
                      readOnly
                    />
                  ) : (
                    <Stack sx={{ height: '100%' }} alignItems="center" justifyContent="center" px={3}>
                      <Typography variant="caption" color="text.disabled" textAlign="center">
                        Select a node above to see the hyperparameters evolution chose for it.
                      </Typography>
                    </Stack>
                  )}
                </Box>
              </>
            )}
          </Box>
        )}
      </Box>
    </Stack>
  )
}

import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import InputAdornment from '@mui/material/InputAdornment'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'

import { api } from '../api/client'
import type { GraphNode } from '../api/types'
import { groupColor } from '../theme'
import HyperparameterField from './HyperparameterField'
import { effectiveValue, isChanged } from './paramDisplay'

interface Props {
  node: GraphNode
  onParamsChange: (params: Record<string, unknown>) => void
  onDelete: () => void
  readOnly?: boolean
}

/**
 * Side panel for the selected node: what the operation is, and a typed editor
 * for every hyperparameter FEDOT knows it accepts.
 *
 * Parameters the tuner explores are listed first — those are the ones that
 * distinguish a hand-built pipeline from a composed one.
 */
export default function NodeInspector({ node, onParamsChange, onDelete, readOnly }: Props) {
  const [filter, setFilter] = useState('')

  const { data: operation, isLoading, error } = useQuery({
    queryKey: ['operation', node.operation],
    queryFn: () => api.operation(node.operation),
    staleTime: Infinity,
  })

  const accent = groupColor(node.group ?? undefined)

  const parameters = useMemo(() => {
    if (!operation) return []
    const needle = filter.trim().toLowerCase()
    const matching = needle
      ? operation.parameters.filter((schema) => schema.name.toLowerCase().includes(needle))
      : operation.parameters
    // Tuned parameters first, then the rest alphabetically.
    return [...matching].sort((a, b) => {
      if (a.tunable !== b.tunable) return a.tunable ? -1 : 1
      return a.name.localeCompare(b.name)
    })
  }, [operation, filter])

  const changedCount = useMemo(
    () =>
      Object.entries(node.params ?? {}).filter(([name, value]) =>
        isChanged(name, value, node.defaults ?? {}),
      ).length,
    [node.params, node.defaults],
  )

  const setParam = (name: string, value: unknown) => {
    onParamsChange({ ...node.params, [name]: value })
  }

  const resetParam = (name: string) => {
    const next = { ...node.params }
    const fallback = operation?.defaults?.[name]
    if (fallback === undefined) {
      delete next[name]
    } else {
      next[name] = fallback
    }
    onParamsChange(next)
  }

  const resetAll = () => onParamsChange({ ...(operation?.defaults ?? {}) })

  return (
    <Stack sx={{ height: '100%', minHeight: 0 }}>
      <Box sx={{ p: 1.75, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Stack direction="row" alignItems="flex-start" spacing={1}>
          <Box sx={{ minWidth: 0, flexGrow: 1 }}>
            <Typography
              variant="h3"
              sx={{ fontFamily: '"JetBrains Mono", monospace', color: accent }}
              noWrap
            >
              {node.operation}
            </Typography>
            {operation?.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.4, fontSize: '0.8rem' }}>
                {operation.description}
              </Typography>
            )}
          </Box>
          {!readOnly && (
            <Tooltip title="Remove this node">
              <Button
                size="small"
                color="error"
                onClick={onDelete}
                startIcon={<DeleteOutlineRoundedIcon fontSize="small" />}
              >
                Remove
              </Button>
            </Tooltip>
          )}
        </Stack>

        <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
          <Chip size="small" label={node.kind ?? 'model'} variant="outlined" />
          {operation?.tasks.map((task) => (
            <Chip key={task} size="small" label={task} variant="outlined" />
          ))}
          {(node.tags ?? []).slice(0, 5).map((tag) => (
            <Chip key={tag} size="small" label={tag} sx={{ height: 20, fontSize: '0.68rem' }} />
          ))}
        </Stack>

        {operation && (
          <Typography sx={{ mt: 0.9, fontSize: '0.72rem', color: 'text.disabled' }}>
            input {operation.input_types.join(', ') || '—'} → output{' '}
            {operation.output_types.join(', ') || '—'}
          </Typography>
        )}
      </Box>

      <Box sx={{ px: 1.75, py: 1.25 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography variant="subtitle2">Hyperparameters</Typography>
          {changedCount > 0 && (
            <Chip
              size="small"
              color="primary"
              label={`${changedCount} changed`}
              sx={{ height: 19, fontSize: '0.68rem' }}
            />
          )}
          <Box sx={{ flexGrow: 1 }} />
          {!readOnly && operation && (
            <Button size="small" onClick={resetAll}>
              Reset all
            </Button>
          )}
        </Stack>

        {operation && operation.parameters.length > 6 && (
          <TextField
            size="small"
            fullWidth
            placeholder="Filter parameters"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            sx={{ mt: 1 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchRoundedIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
          />
        )}
      </Box>

      <Divider />

      <Box sx={{ flexGrow: 1, minHeight: 0, overflowY: 'auto', px: 1, py: 1 }}>
        {isLoading && (
          <Stack alignItems="center" sx={{ py: 4 }}>
            <CircularProgress size={22} />
          </Stack>
        )}

        {error && (
          <Alert severity="error" sx={{ m: 1 }}>
            Could not load the parameter schema for <code>{node.operation}</code>.
          </Alert>
        )}

        {operation && parameters.length === 0 && (
          <Typography sx={{ p: 2, color: 'text.disabled', fontSize: '0.85rem' }}>
            {filter
              ? 'No parameter matches that filter.'
              : 'This operation takes no configurable hyperparameters.'}
          </Typography>
        )}

        <Stack spacing={0.4}>
          {parameters.map((schema) => (
            <HyperparameterField
              key={schema.name}
              schema={schema}
              value={effectiveValue(schema, node.params ?? {})}
              isSet={
                schema.name in (node.params ?? {}) &&
                isChanged(schema.name, node.params[schema.name], node.defaults ?? {})
              }
              onChange={(value) => setParam(schema.name, value)}
              onReset={() => resetParam(schema.name)}
              disabled={readOnly}
            />
          ))}
        </Stack>
      </Box>
    </Stack>
  )
}

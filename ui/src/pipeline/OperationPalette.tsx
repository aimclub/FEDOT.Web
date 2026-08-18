import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Collapse from '@mui/material/Collapse'
import InputAdornment from '@mui/material/InputAdornment'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import ExpandLessRoundedIcon from '@mui/icons-material/ExpandLessRounded'
import ExpandMoreRoundedIcon from '@mui/icons-material/ExpandMoreRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'

import { api } from '../api/client'
import type { OperationSummary } from '../api/types'
import { groupColor } from '../theme'

interface Props {
  task: string | null
  onAdd: (operation: OperationSummary) => void
}

const GROUP_ORDER = [
  'source',
  'preprocessing',
  'feature_engineering',
  'ts_transform',
  'linear',
  'non_linear',
  'tree',
  'ensemble',
  'ts_model',
  'deep',
  'model',
  'data_operation',
]

/** The operation palette, filtered to what the selected task supports. */
export default function OperationPalette({ task, onAdd }: Props) {
  const theme = useTheme()
  const [search, setSearch] = useState('')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  const { data: operations = [], isLoading } = useQuery({
    queryKey: ['operations', task],
    queryFn: () => api.operations(task ? { task } : {}),
    staleTime: Infinity,
  })

  const grouped = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const matching = needle
      ? operations.filter(
          (operation) =>
            operation.id.toLowerCase().includes(needle) ||
            operation.tags.some((tag) => tag.toLowerCase().includes(needle)) ||
            (operation.description ?? '').toLowerCase().includes(needle),
        )
      : operations

    const buckets = new Map<string, OperationSummary[]>()
    for (const operation of matching) {
      const list = buckets.get(operation.group) ?? []
      list.push(operation)
      buckets.set(operation.group, list)
    }
    return [...buckets.entries()].sort(
      (a, b) => GROUP_ORDER.indexOf(a[0]) - GROUP_ORDER.indexOf(b[0]),
    )
  }, [operations, search])

  return (
    <Stack sx={{ height: '100%', minHeight: 0 }}>
      <Box sx={{ p: 1.5, pb: 1 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Operations
          {task && (
            <Typography component="span" sx={{ ml: 0.75, fontSize: '0.72rem', color: 'text.disabled' }}>
              for {task.replace(/_/g, ' ')}
            </Typography>
          )}
        </Typography>
        <TextField
          size="small"
          fullWidth
          placeholder="Search by name or tag"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
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
      </Box>

      <Box sx={{ flexGrow: 1, minHeight: 0, overflowY: 'auto', px: 1, pb: 1.5 }}>
        {isLoading && (
          <Stack alignItems="center" sx={{ py: 4 }}>
            <CircularProgress size={22} />
          </Stack>
        )}

        {!isLoading && grouped.length === 0 && (
          <Typography sx={{ p: 2, fontSize: '0.83rem', color: 'text.disabled' }}>
            No operation matches that search.
          </Typography>
        )}

        {grouped.map(([group, items]) => {
          const accent = groupColor(group)
          const isCollapsed = collapsed[group] ?? false
          return (
            <Box key={group} sx={{ mb: 0.75 }}>
              <Stack
                direction="row"
                alignItems="center"
                spacing={0.75}
                onClick={() => setCollapsed((state) => ({ ...state, [group]: !isCollapsed }))}
                sx={{ px: 0.75, py: 0.5, cursor: 'pointer', borderRadius: 1 }}
              >
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: accent }} />
                <Typography sx={{ fontSize: '0.74rem', fontWeight: 700, color: 'text.secondary' }}>
                  {group.replace(/_/g, ' ')}
                </Typography>
                <Typography sx={{ fontSize: '0.7rem', color: 'text.disabled' }}>
                  {items.length}
                </Typography>
                <Box sx={{ flexGrow: 1 }} />
                {isCollapsed ? (
                  <ExpandMoreRoundedIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                ) : (
                  <ExpandLessRoundedIcon sx={{ fontSize: 16, color: 'text.disabled' }} />
                )}
              </Stack>

              <Collapse in={!isCollapsed}>
                <Stack sx={{ gap: 0.25 }}>
                  {items.map((operation) => (
                    <Tooltip
                      key={operation.id}
                      title={operation.description ?? operation.id}
                      placement="right"
                    >
                      <Stack
                        direction="row"
                        alignItems="center"
                        spacing={0.75}
                        onClick={() => onAdd(operation)}
                        sx={{
                          px: 1,
                          py: 0.55,
                          borderRadius: 1.25,
                          cursor: 'pointer',
                          borderLeft: '2px solid',
                          borderColor: alpha(accent, 0.5),
                          '&:hover': { bgcolor: alpha(accent, 0.12) },
                        }}
                      >
                        <Typography
                          sx={{
                            fontFamily: '"JetBrains Mono", monospace',
                            fontSize: '0.76rem',
                            flexGrow: 1,
                          }}
                          noWrap
                        >
                          {operation.id}
                        </Typography>
                        {!operation.is_default && (
                          <Chip
                            size="small"
                            label="non-default"
                            sx={{
                              height: 15,
                              fontSize: '0.58rem',
                              '& .MuiChip-label': { px: 0.5 },
                              color: theme.palette.warning.main,
                              borderColor: alpha(theme.palette.warning.main, 0.4),
                            }}
                            variant="outlined"
                          />
                        )}
                      </Stack>
                    </Tooltip>
                  ))}
                </Stack>
              </Collapse>
            </Box>
          )
        })}
      </Box>
    </Stack>
  )
}

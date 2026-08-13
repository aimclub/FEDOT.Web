import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import MenuItem from '@mui/material/MenuItem'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'
import ArrowRightAltRoundedIcon from '@mui/icons-material/ArrowRightAltRounded'
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded'
import RemoveCircleOutlineRoundedIcon from '@mui/icons-material/RemoveCircleOutlineRounded'

import { api } from '../api/client'
import type { DatasetRecord } from '../api/types'

interface Props {
  dataset: DatasetRecord
}

const TASKS = [
  { id: 'classification', label: 'Classification' },
  { id: 'regression', label: 'Regression' },
  { id: 'ts_forecasting', label: 'Time series forecasting' },
]

/** Colours by the type a column ends up as, so the before/after reads at a glance. */
const TYPE_COLORS: Record<string, string> = {
  float: '#42a5f5',
  int: '#26a69a',
  str: '#ab47bc',
  bool: '#ffa726',
  NoneType: '#78909c',
}

export default function PreprocessingReport({ dataset }: Props) {
  const theme = useTheme()
  const [task, setTask] = useState(dataset.task ?? 'classification')
  const [enabled, setEnabled] = useState(false)

  const { data: report, isFetching, error } = useQuery({
    queryKey: ['preprocessing', dataset.uid, task],
    queryFn: () => api.preprocessing(dataset.uid, { task }),
    enabled,
    staleTime: Infinity,
    retry: false,
  })

  const featureColumns = dataset.columns.filter((column) => column.name !== dataset.target)

  // Feature order in the report is the file's column order minus the target —
  // unless FEDOT also consumed a column as the index, in which case the counts
  // disagree and positional names would mislabel every column after it.
  const namesAligned = report ? report.columns.before === featureColumns.length : true
  const nameOf = (fileIndex: number): string =>
    namesAligned ? (featureColumns[fileIndex]?.name ?? `column ${fileIndex}`) : `column ${fileIndex}`

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
        <Box>
          <Typography variant="h3">Preprocessing</Typography>
          <Typography variant="caption" color="text.secondary">
            What FEDOT does to this data before any pipeline sees it.
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <TextField
          select
          size="small"
          label="Task"
          value={task}
          onChange={(event) => setTask(event.target.value)}
          sx={{ width: 200 }}
        >
          {TASKS.map((item) => (
            <MenuItem key={item.id} value={item.id}>
              {item.label}
            </MenuItem>
          ))}
        </TextField>
        <Button variant={report ? 'text' : 'contained'} onClick={() => setEnabled(true)} disabled={isFetching}>
          {report ? 'Refresh' : 'Analyse'}
        </Button>
      </Stack>

      {isFetching && (
        <Stack alignItems="center" sx={{ py: 3 }}>
          <CircularProgress size={22} />
        </Stack>
      )}

      {error && <Alert severity="error">{(error as Error).message}</Alert>}

      {report && (
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
            <Chip
              size="small"
              variant="outlined"
              label={`rows ${report.rows.before} → ${report.rows.after}`}
              color={report.rows.before === report.rows.after ? 'default' : 'warning'}
            />
            <Chip
              size="small"
              variant="outlined"
              label={`columns ${report.columns.before} → ${report.columns.after}`}
              color={report.columns.before === report.columns.after ? 'default' : 'warning'}
            />
            {report.target_type && (
              <Chip size="small" variant="outlined" label={`target → ${report.target_type}`} />
            )}
          </Stack>

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
              Columns
            </Typography>
            <Paper variant="outlined" sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Found in the file</TableCell>
                    <TableCell align="right">Gaps</TableCell>
                    <TableCell>Type the pipeline receives</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
  {report.source_types.map((column, index) => {
                    // Rows carry their own file index; the array position is not
                    // trustworthy once any column has been dropped.
                    const fileIndex = Number(column.column ?? index)
                    const found = (column.types as string[] | undefined) ?? []
                    const final = report.final_types[fileIndex]
                    const changed = found.length === 1 && final && found[0] !== final
                    const name = nameOf(fileIndex)
                    return (
                      <TableRow key={fileIndex}>
                        <TableCell>{fileIndex}</TableCell>
                        <TableCell sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.78rem' }}>
                          {name}
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={0.5}>
                            {found.map((type) => (
                              <Chip
                                key={type}
                                size="small"
                                label={type}
                                sx={{
                                  height: 19,
                                  fontSize: '0.68rem',
                                  bgcolor: alpha(TYPE_COLORS[type] ?? theme.palette.text.disabled, 0.16),
                                }}
                              />
                            ))}
                          </Stack>
                        </TableCell>
                        <TableCell align="right">
                          {Number(column.nan_number ?? 0) > 0 ? (
                            <Typography variant="caption" color="warning.main">
                              {String(column.nan_number)}
                            </Typography>
                          ) : (
                            <Typography variant="caption" color="text.disabled">
                              —
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" alignItems="center" spacing={0.5}>
                            {changed && (
                              <ArrowRightAltRoundedIcon
                                sx={{ fontSize: 16, color: 'warning.main' }}
                              />
                            )}
                            {final ? (
                              <Chip
                                size="small"
                                label={final}
                                sx={{
                                  height: 19,
                                  fontSize: '0.68rem',
                                  fontWeight: changed ? 700 : 400,
                                  bgcolor: alpha(TYPE_COLORS[final] ?? theme.palette.text.disabled, 0.22),
                                }}
                              />
                            ) : (
                              <Tooltip title="This column did not survive preprocessing">
                                <Typography variant="caption" color="error">
                                  dropped
                                </Typography>
                              </Tooltip>
                            )}
                          </Stack>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </Paper>
          </Box>

          <Box>
            <Typography variant="subtitle2" sx={{ mb: 0.75 }}>
              Decisions
            </Typography>
            <Stack spacing={0.5}>
              {report.steps.map((step) => (
                <Stack
                  key={step.id}
                  direction="row"
                  spacing={1}
                  alignItems="flex-start"
                  sx={{
                    px: 1.25,
                    py: 0.75,
                    borderRadius: 1.5,
                    bgcolor: step.applied ? alpha(theme.palette.primary.main, 0.06) : 'transparent',
                    opacity: step.applied ? 1 : 0.55,
                  }}
                >
                  {step.applied ? (
                    <CheckCircleRoundedIcon sx={{ fontSize: 16, color: 'primary.main', mt: 0.2 }} />
                  ) : (
                    <RemoveCircleOutlineRoundedIcon
                      sx={{ fontSize: 16, color: 'text.disabled', mt: 0.2 }}
                    />
                  )}
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="body2">{step.title}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {step.detail}
                    </Typography>
                    {step.applied && step.columns.length > 0 && (
                      <Stack direction="row" spacing={0.5} sx={{ mt: 0.5, flexWrap: 'wrap', gap: 0.4 }}>
                        {step.columns.map((column) => (
                          <Chip
                            key={column}
                            size="small"
                            variant="outlined"
                            label={nameOf(column)}
                            sx={{ height: 18, fontSize: '0.65rem' }}
                          />
                        ))}
                      </Stack>
                    )}
                  </Box>
                </Stack>
              ))}
            </Stack>
          </Box>

          <Typography variant="caption" color="text.disabled">
            {report.note}
          </Typography>
        </Stack>
      )}
    </Paper>
  )
}

import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import LinearProgress from '@mui/material/LinearProgress'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { alpha, useTheme } from '@mui/material/styles'

import type { ObjectiveResult } from '../api/types'
import { useAnalysis } from './useAnalysis'

interface Props {
  runUid: string
  open: boolean
  onClose: () => void
}

const show = (value: number | null | undefined, digits = 4): string =>
  value === null || value === undefined ? '—' : Number(value.toFixed(digits)).toString()

/**
 * Where the objective value came from.
 *
 * FEDOT scores a pipeline on each cross-validation fold and averages the results;
 * that average is the fitness evolution compares pipelines by, and the folds
 * behind it are discarded. They are recomputed here on the same split the
 * composer used, so the mean below is the number the run actually optimised —
 * shown next to the spread across folds, which says how much to trust it.
 */
export default function ObjectiveBreakdown({ runUid, open, onClose }: Props) {
  const theme = useTheme()
  const { start, startError, record, isRunning, isCached } = useAnalysis(runUid, 'objective')

  const result = record?.status === 'finished' ? (record.result as ObjectiveResult) : null

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle sx={{ pb: 1 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Box>
            <Typography variant="h2" component="span">
              Objective breakdown
            </Typography>
            <Typography variant="body2" color="text.secondary">
              How the fitness value evolution compared pipelines by was computed.
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          {result && isCached && (
            <Tooltip title="Shown from an earlier run of this analysis">
              <Chip size="small" variant="outlined" label="cached" />
            </Tooltip>
          )}
          {result && <Chip size="small" variant="outlined" label={`${result.cv_folds} folds`} />}
        </Stack>
      </DialogTitle>

      <DialogContent dividers>
        {!record && !isRunning && (
          <Stack spacing={2} alignItems="flex-start">
            <Typography variant="body2" color="text.secondary">
              Refits the run's best pipeline on each cross-validation fold and scores it, then
              scores it once more on the holdout. That takes as long as a handful of fits.
            </Typography>
            <Button variant="contained" onClick={() => start()}>
              Compute breakdown
            </Button>
          </Stack>
        )}

        {isRunning && (
          <Box sx={{ py: 3 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
              Refitting the pipeline on each fold…
            </Typography>
          </Box>
        )}

        {startError && <Alert severity="error">{startError}</Alert>}
        {record?.status === 'failed' && <Alert severity="error">{record.error}</Alert>}

        {result && (
          <Stack spacing={2.5}>
            <Paper variant="outlined" sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Fold</TableCell>
                    <TableCell align="right">Train</TableCell>
                    <TableCell align="right">Test</TableCell>
                    {result.metrics.map((metric) => (
                      <TableCell key={metric} align="right">
                        {metric}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.folds.map((fold) => (
                    <TableRow key={fold.fold}>
                      <TableCell>{fold.fold + 1}</TableCell>
                      {fold.failed ? (
                        <TableCell colSpan={2 + result.metrics.length}>
                          <Typography variant="caption" color="error">
                            failed: {fold.error}
                          </Typography>
                        </TableCell>
                      ) : (
                        <>
                          <TableCell align="right">{fold.train_size}</TableCell>
                          <TableCell align="right">{fold.test_size}</TableCell>
                          {result.metrics.map((metric) => (
                            <TableCell
                              key={metric}
                              align="right"
                              sx={{ fontFamily: '"JetBrains Mono", monospace' }}
                            >
                              {show(fold.readable?.[metric])}
                            </TableCell>
                          ))}
                        </>
                      )}
                    </TableRow>
                  ))}

                  <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
                    <TableCell colSpan={3}>
                      <Tooltip title="The mean over folds — this is the objective value evolution used">
                        <Typography variant="subtitle2">mean over folds</Typography>
                      </Tooltip>
                    </TableCell>
                    {result.metrics.map((metric) => {
                      const summary = result.summary[metric]
                      return (
                        <TableCell
                          key={metric}
                          align="right"
                          sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 700 }}
                        >
                          {show(summary?.readable_mean)}
                        </TableCell>
                      )
                    })}
                  </TableRow>

                  <TableRow>
                    <TableCell colSpan={3}>
                      <Tooltip title="Largest minus smallest across folds — a wide spread means the score is unstable">
                        <Typography variant="caption" color="text.secondary">
                          spread across folds
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    {result.metrics.map((metric) => (
                      <TableCell
                        key={metric}
                        align="right"
                        sx={{ fontFamily: '"JetBrains Mono", monospace', color: 'text.secondary' }}
                      >
                        {show(result.summary[metric]?.spread)}
                      </TableCell>
                    ))}
                  </TableRow>

                  <TableRow sx={{ bgcolor: alpha(theme.palette.success.main, 0.08) }}>
                    <TableCell colSpan={3}>
                      <Tooltip title="Data neither evolution nor the folds ever saw">
                        <Typography variant="subtitle2">
                          holdout (n={result.holdout.size})
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    {result.metrics.map((metric) => (
                      <TableCell
                        key={metric}
                        align="right"
                        sx={{ fontFamily: '"JetBrains Mono", monospace', fontWeight: 700 }}
                      >
                        {show(result.holdout.readable?.[metric])}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableBody>
              </Table>
            </Paper>

            {result.holdout.error && (
              <Alert severity="warning">Holdout scoring failed: {result.holdout.error}</Alert>
            )}

            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.75 }}>
              {result.primary_metric && (
                <Chip
                  size="small"
                  color="primary"
                  label={`optimised for ${result.primary_metric}`}
                />
              )}
              {result.metrics
                .filter((metric) => metric !== result.primary_metric)
                .map((metric) => (
                  <Chip key={metric} size="small" variant="outlined" label={metric} />
                ))}
            </Stack>

            <Typography variant="caption" color="text.disabled">
              {result.note}
            </Typography>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        {result && (
          <Button onClick={() => start()} disabled={isRunning}>
            Recompute
          </Button>
        )}
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}

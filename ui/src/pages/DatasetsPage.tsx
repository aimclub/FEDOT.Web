import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import IconButton from '@mui/material/IconButton'
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
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded'

import { api } from '../api/client'
import type { DatasetRecord } from '../api/types'
import PreprocessingReport from '../datasets/PreprocessingReport'

const TYPE_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'warning'> = {
  numeric: 'primary',
  categorical: 'secondary',
  categorical_numeric: 'secondary',
  empty: 'warning',
}

export default function DatasetsPage() {
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: api.datasets,
  })

  const { data: preview } = useQuery({
    queryKey: ['dataset-preview', selected],
    queryFn: () => api.datasetPreview(selected!),
    enabled: Boolean(selected),
  })

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDataset(file),
    onSuccess: (record) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      setSelected(record.uid)
      setError(null)
    },
    onError: (uploadError: Error) => setError(uploadError.message),
  })

  const updateTarget = useMutation({
    mutationFn: ({ uid, target }: { uid: string; target: string }) =>
      api.updateDataset(uid, { target }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['datasets'] }),
    onError: (updateError: Error) => setError(updateError.message),
  })

  const remove = useMutation({
    mutationFn: (uid: string) => api.deleteDataset(uid),
    onSuccess: (_, uid) => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      if (selected === uid) setSelected(null)
    },
  })

  const current = datasets.find((dataset) => dataset.uid === selected) ?? null

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Typography variant="h1">Datasets</Typography>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          startIcon={<UploadFileRoundedIcon />}
          onClick={() => fileInput.current?.click()}
          disabled={upload.isPending}
        >
          {upload.isPending ? 'Uploading…' : 'Upload CSV'}
        </Button>
        <input
          ref={fileInput}
          type="file"
          accept=".csv,.tsv,.txt"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) upload.mutate(file)
            event.target.value = ''
          }}
        />
      </Stack>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {isLoading && <CircularProgress size={24} />}

      {!isLoading && datasets.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No datasets yet. Upload a CSV whose columns are features plus one target column.
          </Typography>
        </Paper>
      )}

      {datasets.length > 0 && (
        <Paper variant="outlined" sx={{ mb: 3 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell align="right">Rows</TableCell>
                <TableCell align="right">Columns</TableCell>
                <TableCell>Target</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {datasets.map((dataset: DatasetRecord) => (
                <TableRow
                  key={dataset.uid}
                  hover
                  selected={dataset.uid === selected}
                  onClick={() => setSelected(dataset.uid)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{dataset.name}</TableCell>
                  <TableCell align="right">{dataset.n_rows ?? '—'}</TableCell>
                  <TableCell align="right">{dataset.n_columns ?? '—'}</TableCell>
                  <TableCell onClick={(event) => event.stopPropagation()}>
                    <TextField
                      select
                      size="small"
                      variant="standard"
                      value={dataset.target ?? ''}
                      onChange={(event) =>
                        updateTarget.mutate({ uid: dataset.uid, target: event.target.value })
                      }
                      sx={{ minWidth: 120 }}
                    >
                      {dataset.columns.map((column) => (
                        <MenuItem key={column.name} value={column.name}>
                          {column.name}
                        </MenuItem>
                      ))}
                    </TextField>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(dataset.created_at).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                    <Tooltip title="Delete this dataset">
                      <IconButton size="small" onClick={() => remove.mutate(dataset.uid)}>
                        <DeleteOutlineRoundedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {current && preview && (
        <>
          <Typography variant="h2" sx={{ mb: 1 }}>
            {current.name}
          </Typography>
          <Stack direction="row" spacing={0.75} sx={{ mb: 1.5, flexWrap: 'wrap', gap: 0.75 }}>
            {preview.columns.map((column) => (
              <Tooltip
                key={column.name}
                title={`${column.missing_sample} missing and ${column.distinct_sample} distinct values in the sampled rows`}
              >
                <Chip
                  size="small"
                  color={column.name === current.target ? 'success' : TYPE_COLORS[column.type] ?? 'default'}
                  variant={column.name === current.target ? 'filled' : 'outlined'}
                  label={`${column.name} · ${column.type}`}
                />
              </Tooltip>
            ))}
          </Stack>

          <Paper variant="outlined" sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  {preview.columns.map((column) => (
                    <TableCell key={column.name} sx={{ whiteSpace: 'nowrap' }}>
                      {column.name}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {preview.preview.map((row, index) => (
                  <TableRow key={index}>
                    {preview.columns.map((column) => (
                      <TableCell
                        key={column.name}
                        sx={{ fontFamily: '"JetBrains Mono", monospace', fontSize: '0.75rem' }}
                      >
                        {String(row[column.name] ?? '')}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
          <Typography variant="caption" color="text.disabled" sx={{ mt: 1, display: 'block' }}>
            Showing the first {preview.preview.length} of {preview.n_rows} rows.
          </Typography>

          <Box sx={{ mt: 3 }}>
            <PreprocessingReport dataset={current} />
          </Box>
        </>
      )}
    </Box>
  )
}

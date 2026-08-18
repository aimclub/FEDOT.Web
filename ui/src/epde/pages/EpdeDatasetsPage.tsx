import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Grid from '@mui/material/Grid'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import DeleteRoundedIcon from '@mui/icons-material/DeleteRounded'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded'
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded'

import { epdeApi } from '../api/client'
import AxisEditor from '../datasets/AxisEditor'
import FieldPreview from '../datasets/FieldPreview'

export default function EpdeDatasetsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const { data: capabilities } = useQuery({
    queryKey: ['epde-capabilities'],
    queryFn: epdeApi.capabilities,
    staleTime: Infinity,
  })
  const { data: datasets, isLoading } = useQuery({
    queryKey: ['epde-datasets'],
    queryFn: epdeApi.datasets,
  })

  const active = datasets?.find((dataset) => dataset.uid === selected) ?? datasets?.[0] ?? null

  const { data: preview } = useQuery({
    queryKey: ['epde-preview', active?.uid],
    queryFn: () => epdeApi.preview(active!.uid),
    enabled: Boolean(active),
  })

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['epde-datasets'] })
    queryClient.invalidateQueries({ queryKey: ['epde-preview'] })
  }

  const upload = useMutation({
    mutationFn: (file: File) => epdeApi.uploadDataset(file),
    onSuccess: (record) => {
      setUploadError(null)
      setSelected(record.uid)
      refresh()
    },
    onError: (error: Error) => setUploadError(error.message),
  })

  const createSample = useMutation({
    mutationFn: (sampleId: string) => epdeApi.createSample(sampleId),
    onSuccess: (record) => {
      setSelected(record.uid)
      refresh()
    },
  })

  const remove = useMutation({
    mutationFn: (uid: string) => epdeApi.deleteDataset(uid),
    onSuccess: () => {
      setSelected(null)
      refresh()
    },
  })

  const saveAxes = useMutation({
    mutationFn: (axes: { name: string; start: number; stop: number }[]) =>
      epdeApi.updateAxes(active!.uid, axes),
    onSuccess: refresh,
  })

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2 }}>
        <Typography variant="h1" sx={{ fontSize: '1.25rem' }}>
          Fields
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <input
          ref={fileInput}
          type="file"
          hidden
          accept=".npy,.npz,.csv,.txt,.tsv,.dat"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) upload.mutate(file)
            event.target.value = ''
          }}
        />
        <Button
          size="small"
          variant="outlined"
          startIcon={<UploadFileRoundedIcon />}
          onClick={() => fileInput.current?.click()}
          disabled={upload.isPending}
        >
          Upload a field
        </Button>
      </Stack>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 760 }}>
        A search needs a variable sampled on a grid, plus the coordinates of that grid. Upload a{' '}
        <code>.npy</code> array, an <code>.npz</code> bundle of the field and its coordinate
        vectors, or a CSV — either a numeric matrix or a table with a time column. The coordinates
        are not decoration: every derivative EPDE takes, and therefore every coefficient it reports,
        scales with the grid spacing.
      </Typography>

      {uploadError && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setUploadError(null)}>
          {uploadError}
        </Alert>
      )}

      {capabilities && !capabilities.epde_available && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {capabilities.epde_error} Fields can still be uploaded and inspected; starting a search
          needs the framework.
        </Alert>
      )}

      {(datasets?.length ?? 0) === 0 && capabilities && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Typography variant="h3" sx={{ mb: 0.5 }}>
            Start from a known equation
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            Each of these is an exact solution of an equation stated below it, so a run can be
            judged rather than admired.
          </Typography>
          <Grid container spacing={1.5}>
            {capabilities.samples.map((sample) => (
              <Grid key={sample.id} size={{ xs: 12, sm: 6, md: 3 }}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardActionArea
                    sx={{ height: '100%' }}
                    onClick={() => createSample.mutate(sample.id)}
                  >
                    <CardContent>
                      <Typography variant="subtitle2">{sample.name}</Typography>
                      <Typography variant="caption" color="text.secondary" component="p">
                        {sample.description}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          mt: 1,
                          display: 'block',
                          fontFamily: '"JetBrains Mono", monospace',
                          color: 'primary.main',
                        }}
                      >
                        {sample.expected}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {isLoading && (
        <Stack alignItems="center" sx={{ py: 6 }}>
          <CircularProgress size={24} />
        </Stack>
      )}

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={1}>
            {datasets?.map((dataset) => (
              <Paper
                key={dataset.uid}
                variant="outlined"
                sx={{
                  p: 1.5,
                  cursor: 'pointer',
                  borderColor: dataset.uid === active?.uid ? 'primary.main' : 'divider',
                }}
                onClick={() => setSelected(dataset.uid)}
              >
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Box sx={{ minWidth: 0, flexGrow: 1 }}>
                    <Typography variant="subtitle2" noWrap>
                      {dataset.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dataset.variables.map((variable) => variable.name).join(', ')} ·{' '}
                      {dataset.shape.join(' × ')} on {dataset.axes.map((axis) => axis.name).join(', ')}
                    </Typography>
                  </Box>
                  <Tooltip title="Delete this field">
                    <IconButton
                      size="small"
                      onClick={(event) => {
                        event.stopPropagation()
                        remove.mutate(dataset.uid)
                      }}
                    >
                      <DeleteRoundedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Stack>
                {dataset.warnings.length > 0 && (
                  <Chip
                    size="small"
                    color="warning"
                    variant="outlined"
                    label="grid needs attention"
                    sx={{ mt: 0.75 }}
                  />
                )}
              </Paper>
            ))}
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          {active && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1.5 }}>
                <Typography variant="h3">{active.name}</Typography>
                <Box sx={{ flexGrow: 1 }} />
                <Tooltip title="Download the normalised field, coordinates included">
                  <IconButton
                    size="small"
                    component="a"
                    href={epdeApi.datasetExportUrl(active.uid)}
                    download
                  >
                    <DownloadRoundedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<PlayArrowRoundedIcon />}
                  disabled={!capabilities?.epde_available}
                  onClick={() => navigate(`/epde/runs/new?dataset=${active.uid}`)}
                >
                  Search for an equation
                </Button>
              </Stack>

              {active.note && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                  {active.note}
                </Typography>
              )}

              {active.warnings.map((warning, index) => (
                <Alert key={index} severity="warning" variant="outlined" sx={{ mb: 1 }}>
                  {warning}
                </Alert>
              ))}

              {preview && <FieldPreview preview={preview} />}

              <Divider sx={{ my: 2 }} />

              <Typography variant="h3" sx={{ mb: 1 }}>
                Grid
              </Typography>
              <AxisEditor
                axes={active.axes}
                onSave={(axes) => saveAxes.mutateAsync(axes)}
              />

              <Divider sx={{ my: 2 }} />

              <Typography variant="h3" sx={{ mb: 1 }}>
                Variables
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {active.variables.map((variable) => (
                  <Chip
                    key={variable.name}
                    size="small"
                    variant="outlined"
                    label={`${variable.name} ∈ [${Number(variable.min ?? 0).toPrecision(3)}, ${Number(
                      variable.max ?? 0,
                    ).toPrecision(3)}]`}
                  />
                ))}
              </Stack>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

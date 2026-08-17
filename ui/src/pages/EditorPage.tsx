import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import MenuItem from '@mui/material/MenuItem'
import Paper from '@mui/material/Paper'
import Snackbar from '@mui/material/Snackbar'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import CheckCircleRoundedIcon from '@mui/icons-material/CheckCircleRounded'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'
import ErrorRoundedIcon from '@mui/icons-material/ErrorRounded'
import NoteAddRoundedIcon from '@mui/icons-material/NoteAddRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import SwapHorizRoundedIcon from '@mui/icons-material/SwapHorizRounded'
import SwapVertRoundedIcon from '@mui/icons-material/SwapVertRounded'
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded'

import { api } from '../api/client'
import type { OperationSummary } from '../api/types'
import NodeInspector from '../pipeline/NodeInspector'
import OperationPalette from '../pipeline/OperationPalette'
import PipelineCanvas from '../pipeline/PipelineCanvas'
import { useEditorStore } from '../pipeline/editorStore'
import type { LayoutDirection } from '../pipeline/layout'

const TASKS = [
  { id: 'classification', label: 'Classification' },
  { id: 'regression', label: 'Regression' },
  { id: 'ts_forecasting', label: 'Time series forecasting' },
]

export default function EditorPage() {
  const { uid } = useParams<{ uid?: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)

  const [direction, setDirection] = useState<LayoutDirection>('LR')
  const [toast, setToast] = useState<{ message: string; severity: 'success' | 'error' | 'info' } | null>(
    null,
  )

  const {
    graph,
    task,
    name,
    selectedNodeId,
    validation,
    dirty,
    pipelineUid,
    setGraph,
    setTask,
    setName,
    setValidation,
    select,
    addOperation,
    removeNode,
    setNodeParams,
    connect,
    disconnect,
    reset,
  } = useEditorStore()

  // Loading an existing pipeline into the editor.
  const { data: stored } = useQuery({
    queryKey: ['pipeline', uid],
    queryFn: () => api.pipeline(uid!),
    enabled: Boolean(uid),
  })

  useEffect(() => {
    if (stored?.graph) {
      setGraph(stored.graph, { name: stored.name, uid: stored.uid, clean: true })
      if (stored.task) setTask(stored.task)
    }
  }, [stored, setGraph, setTask])

  useEffect(() => {
    // "Open in editor" sets the store first and navigates here after, so a
    // blind reset on mount would wipe exactly what was handed over — and a
    // route change must not destroy unsaved work either. Only a clean store
    // is cleared.
    if (!uid && !useEditorStore.getState().dirty) reset()
  }, [uid, reset])

  const selectedNode = useMemo(
    () => graph.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [graph.nodes, selectedNodeId],
  )

  const validate = useMutation({
    mutationFn: () => api.validatePipeline(graph, task),
    onSuccess: (result) => {
      setValidation(result)
      setToast({
        message: result.is_valid
          ? `Valid pipeline — depth ${result.depth}, ${result.length} nodes`
          : result.problems[0] ?? 'The pipeline is not valid',
        severity: result.is_valid ? 'success' : 'error',
      })
    },
    onError: (error: Error) => setToast({ message: error.message, severity: 'error' }),
  })

  const save = useMutation({
    mutationFn: () =>
      api.savePipeline({ name, task, graph, ...(pipelineUid ? { uid: pipelineUid } : {}) }),
    onSuccess: (record) => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] })
      setGraph(record.graph!, { name: record.name, uid: record.uid, clean: true })
      setToast({ message: 'Pipeline saved', severity: 'success' })
      if (!uid) navigate(`/editor/${record.uid}`, { replace: true })
    },
    onError: (error: Error) => setToast({ message: error.message, severity: 'error' }),
  })

  const handleAdd = async (operation: OperationSummary) => {
    try {
      // The palette summary carries no defaults; fetch them so a new node starts
      // from exactly what FEDOT would apply.
      const detail = await api.operation(operation.id)
      addOperation(operation, detail.defaults)
    } catch {
      addOperation(operation, {})
    }
  }

  const handleImport = async (file: File) => {
    try {
      const payload = JSON.parse(await file.text())
      const imported = await api.importPipeline(payload)
      setGraph(imported, { name: file.name.replace(/\.json$/i, ''), uid: null })
      setToast({ message: `Imported ${imported.nodes.length} nodes`, severity: 'success' })
    } catch (error) {
      setToast({ message: (error as Error).message, severity: 'error' })
    }
  }

  const problems = useMemo(() => {
    const map: Record<string, string> = {}
    if (!validation || validation.is_valid) return map
    // Rule failures are pipeline-wide; mark the roots so the warning is visible.
    for (const node of graph.nodes) {
      if (node.is_root) map[node.id] = validation.problems[0] ?? 'Invalid pipeline'
    }
    return map
  }, [validation, graph.nodes])

  return (
    <Box sx={{ display: 'flex', height: '100%', minHeight: 0 }}>
      <Paper
        square
        elevation={0}
        sx={{ width: 268, flexShrink: 0, borderRight: '1px solid', borderColor: 'divider' }}
      >
        <OperationPalette task={task} onAdd={handleAdd} />
      </Paper>

      <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
          sx={{ px: 1.5, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}
        >
          <TextField
            size="small"
            value={name}
            onChange={(event) => setName(event.target.value)}
            sx={{ width: 230 }}
          />
          <TextField
            size="small"
            select
            label="Task"
            value={task ?? ''}
            onChange={(event) => setTask(event.target.value || null)}
            sx={{ width: 180 }}
          >
            <MenuItem value="">Any</MenuItem>
            {TASKS.map((item) => (
              <MenuItem key={item.id} value={item.id}>
                {item.label}
              </MenuItem>
            ))}
          </TextField>

          <Divider orientation="vertical" flexItem />

          <Chip size="small" variant="outlined" label={`${graph.nodes.length} nodes`} />
          <Chip size="small" variant="outlined" label={`depth ${graph.depth || '—'}`} />
          {dirty && <Chip size="small" color="warning" variant="outlined" label="unsaved" />}

          <Box sx={{ flexGrow: 1 }} />

          <ToggleButtonGroup
            size="small"
            exclusive
            value={direction}
            onChange={(_, value) => value && setDirection(value)}
          >
            <ToggleButton value="LR">
              <Tooltip title="Left to right">
                <SwapHorizRoundedIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="TB">
              <Tooltip title="Top to bottom">
                <SwapVertRoundedIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>

          <Tooltip title="Load a pipeline saved by FEDOT">
            <IconButton size="small" onClick={() => fileInput.current?.click()}>
              <UploadFileRoundedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <input
            ref={fileInput}
            type="file"
            accept="application/json,.json"
            hidden
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void handleImport(file)
              event.target.value = ''
            }}
          />

          {pipelineUid && (
            <Tooltip title="Download in FEDOT's own JSON format">
              <IconButton size="small" component="a" href={api.exportPipelineUrl(pipelineUid)}>
                <DownloadRoundedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          <Tooltip title="Start a new pipeline">
            <IconButton
              size="small"
              onClick={() => {
                reset()
                navigate('/editor')
              }}
            >
              <NoteAddRoundedIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          <Button
            size="small"
            variant="outlined"
            onClick={() => validate.mutate()}
            disabled={graph.nodes.length === 0 || validate.isPending}
            startIcon={
              validation ? (
                validation.is_valid ? (
                  <CheckCircleRoundedIcon fontSize="small" color="success" />
                ) : (
                  <ErrorRoundedIcon fontSize="small" color="error" />
                )
              ) : undefined
            }
          >
            Validate
          </Button>
          <Button
            size="small"
            variant="contained"
            startIcon={<SaveRoundedIcon fontSize="small" />}
            onClick={() => save.mutate()}
            disabled={graph.nodes.length === 0 || save.isPending}
          >
            Save
          </Button>
        </Stack>

        {validation && !validation.is_valid && (
          <Alert severity="error" square sx={{ borderRadius: 0, py: 0.4 }}>
            {validation.problems.map((problem) => (
              <div key={problem}>{problem}</div>
            ))}
          </Alert>
        )}

        <Box sx={{ flexGrow: 1, minHeight: 0 }}>
          <PipelineCanvas
            graph={graph}
            direction={direction}
            selectedNodeId={selectedNodeId}
            problems={problems}
            onSelect={select}
            onConnect={(source, target) => {
              const error = connect(source, target)
              if (error) setToast({ message: error, severity: 'error' })
            }}
            onDisconnect={disconnect}
            emptyHint="Pick an operation on the left to place the first node. Drag from a node's right edge to connect it to the next one."
          />
        </Box>
      </Box>

      <Paper
        square
        elevation={0}
        sx={{ width: 372, flexShrink: 0, borderLeft: '1px solid', borderColor: 'divider' }}
      >
        {selectedNode ? (
          <NodeInspector
            node={selectedNode}
            onParamsChange={(params) => setNodeParams(selectedNode.id, params)}
            onDelete={() => removeNode(selectedNode.id)}
          />
        ) : (
          <Stack sx={{ height: '100%' }} alignItems="center" justifyContent="center" spacing={1} px={3}>
            <Typography variant="body2" color="text.disabled" textAlign="center">
              Select a node to inspect and edit its hyperparameters.
            </Typography>
            <Typography variant="caption" color="text.disabled" textAlign="center">
              Every parameter is rendered from the schema FEDOT publishes for that operation, bounded
              by the same sampling scope its tuner searches.
            </Typography>
          </Stack>
        )}
      </Paper>

      <Snackbar
        open={Boolean(toast)}
        autoHideDuration={4500}
        onClose={() => setToast(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {toast ? (
          <Alert severity={toast.severity} onClose={() => setToast(null)} variant="filled">
            {toast.message}
          </Alert>
        ) : undefined}
      </Snackbar>
    </Box>
  )
}

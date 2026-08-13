import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import AddRoundedIcon from '@mui/icons-material/AddRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'

import { api } from '../api/client'

export default function PipelinesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: pipelines = [], isLoading } = useQuery({
    queryKey: ['pipelines'],
    queryFn: () => api.pipelines(),
  })

  const remove = useMutation({
    mutationFn: (uid: string) => api.deletePipeline(uid),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pipelines'] }),
  })

  return (
    <Box sx={{ height: '100%', overflowY: 'auto', p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 2 }}>
        <Box>
          <Typography variant="h1">Saved pipelines</Typography>
          <Typography variant="body2" color="text.secondary">
            Pipelines you built by hand, and the best pipeline from every finished run.
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Button variant="contained" startIcon={<AddRoundedIcon />} onClick={() => navigate('/editor')}>
          New pipeline
        </Button>
      </Stack>

      {isLoading && <CircularProgress size={24} />}

      {!isLoading && pipelines.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            Nothing saved yet. Build one in the editor, or run a composition.
          </Typography>
        </Paper>
      )}

      {pipelines.length > 0 && (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Origin</TableCell>
                <TableCell>Task</TableCell>
                <TableCell align="right">Nodes</TableCell>
                <TableCell align="right">Depth</TableCell>
                <TableCell>Updated</TableCell>
                <TableCell align="right" />
              </TableRow>
            </TableHead>
            <TableBody>
              {pipelines.map((pipeline) => (
                <TableRow
                  key={pipeline.uid}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/editor/${pipeline.uid}`)}
                >
                  <TableCell>{pipeline.name}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      variant="outlined"
                      color={pipeline.origin === 'automl' ? 'primary' : 'default'}
                      label={pipeline.origin ?? 'editor'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">{pipeline.task ?? '—'}</Typography>
                  </TableCell>
                  <TableCell align="right">{pipeline.length}</TableCell>
                  <TableCell align="right">{pipeline.depth}</TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(pipeline.updated_at).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" onClick={(event) => event.stopPropagation()}>
                    <Tooltip title="Download in FEDOT's JSON format">
                      <IconButton
                        size="small"
                        component="a"
                        href={api.exportPipelineUrl(pipeline.uid)}
                      >
                        <DownloadRoundedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => remove.mutate(pipeline.uid)}>
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
    </Box>
  )
}

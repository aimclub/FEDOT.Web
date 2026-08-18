import { useEffect, useState } from 'react'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import type { AxisInfo } from '../api/types'

/**
 * The coordinate grid, which is half the input rather than metadata.
 *
 * EPDE differentiates with respect to these coordinates, so a field uploaded
 * without them — the common case for a bare `.npy` — arrives with axes running
 * 0, 1, 2, … A first derivative is then wrong by the true spacing and a second
 * by its square. The discovered *structure* survives that; every coefficient
 * does not, which is the kind of error that produces a publishable-looking
 * equation with meaningless numbers.
 */

interface Props {
  axes: AxisInfo[]
  disabled?: boolean
  onSave: (axes: { name: string; start: number; stop: number }[]) => Promise<unknown>
}

export default function AxisEditor({ axes, disabled, onSave }: Props) {
  const [draft, setDraft] = useState(() => axes.map(toDraft))
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => setDraft(axes.map(toDraft)), [axes])

  const dirty = draft.some((axis, index) => {
    const original = toDraft(axes[index])
    return (
      axis.name !== original.name || axis.start !== original.start || axis.stop !== original.stop
    )
  })

  const save = async () => {
    setSaving(true)
    setError(null)
    try {
      await onSave(
        draft.map((axis) => ({
          name: axis.name.trim(),
          start: Number(axis.start),
          stop: Number(axis.stop),
        })),
      )
    } catch (problem) {
      setError((problem as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const uneven = axes.filter((axis) => !axis.uniform)

  return (
    <Stack spacing={1.5}>
      {uneven.length > 0 && (
        <Alert severity="warning" variant="outlined">
          {uneven.map((axis) => axis.name).join(', ')}{' '}
          {uneven.length === 1 ? 'is' : 'are'} not evenly spaced. EPDE&apos;s derivative
          preprocessors assume an even grid, so the derivatives — and every coefficient derived from
          them — will be biased. Resample before running a search.
        </Alert>
      )}

      {draft.map((axis, index) => (
        <Stack key={index} direction="row" spacing={1.25} alignItems="center">
          <TextField
            size="small"
            label={`Axis ${index}`}
            value={axis.name}
            disabled={disabled}
            onChange={(event) =>
              setDraft((current) =>
                current.map((item, position) =>
                  position === index ? { ...item, name: event.target.value } : item,
                ),
              )
            }
            sx={{ width: 120 }}
          />
          <TextField
            size="small"
            label="From"
            type="number"
            value={axis.start}
            disabled={disabled}
            onChange={(event) =>
              setDraft((current) =>
                current.map((item, position) =>
                  position === index ? { ...item, start: event.target.value } : item,
                ),
              )
            }
            sx={{ width: 130 }}
          />
          <TextField
            size="small"
            label="To"
            type="number"
            value={axis.stop}
            disabled={disabled}
            onChange={(event) =>
              setDraft((current) =>
                current.map((item, position) =>
                  position === index ? { ...item, stop: event.target.value } : item,
                ),
              )
            }
            sx={{ width: 130 }}
          />
          <Typography variant="caption" color="text.disabled">
            {axes[index]?.size} points
            {axes[index]?.step != null && ` · step ${Number(axes[index].step).toPrecision(3)}`}
          </Typography>
        </Stack>
      ))}

      {error && <Alert severity="error">{error}</Alert>}

      <Stack direction="row" spacing={1} alignItems="center">
        <Button size="small" variant="outlined" disabled={!dirty || saving || disabled} onClick={save}>
          {saving ? 'Saving…' : 'Save grid'}
        </Button>
        <Typography variant="caption" color="text.disabled">
          The number of points is fixed by the data; only the range and the names can change.
        </Typography>
      </Stack>
    </Stack>
  )
}

const toDraft = (axis: AxisInfo | undefined) => ({
  name: axis?.name ?? '',
  start: String(axis?.start ?? 0),
  stop: String(axis?.stop ?? 0),
})

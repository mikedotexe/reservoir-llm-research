import { useMemo } from 'react';
import CoordinateInspector from './CoordinateInspector';
import RecordedStateSpectrum from './RecordedStateSpectrum';
import RecordedTrajectory from './RecordedTrajectory';
import SurfaceView from './SurfaceView';
import { REFERENCE_FIELDS, referenceFieldDefinition, selectReferenceField, type ReferenceField } from './referenceFieldMath';
import type { ObservatoryStateFrame, ObservatoryStateReference, ObservatoryTimelinePoint } from './observatoryTypes';
import type { CameraPose, ReferenceScene } from './types';

export interface StateInspectionPreferences { field: ReferenceField; modes: number; projection: number }
export const INITIAL_STATE_INSPECTION: StateInspectionPreferences = { field: 'signedActivation', modes: 3, projection: 0 };
interface Props {
  state: ObservatoryStateFrame; reference: ObservatoryStateReference | null;
  points: ObservatoryTimelinePoint[]; total: number; row: number; node: number;
  pose: CameraPose; tableOnly: boolean; preferences: StateInspectionPreferences;
  onPreferences: (value: StateInspectionPreferences) => void;
  onRow: (index: number) => void; onNode: (index: number) => void; onPose: (pose: CameraPose) => void;
}
const exact = (value: number | null | undefined) => value == null || !Number.isFinite(value) ? 'Unavailable' : Object.is(value, -0) ? '-0' : String(value);

export default function RecordedStateInspection({ state, reference, points, total, row, node, pose, tableOnly, preferences, onPreferences, onRow, onNode, onPose }: Props) {
  const wantedModes = preferences.modes === 3 ? '0,1,2' : String(preferences.modes);
  const selectedModes = state.fields?.selections.find(selection => selection.selectedModes.join(',') === wantedModes);
  const selected = useMemo(() => selectReferenceField(preferences.field, {
    activations: state.activations, magnitude: state.fields?.magnitude, deviation: state.fields?.deviation,
    reconstruction: selectedModes?.reconstruction, residual: selectedModes?.residual,
  }), [state, selectedModes, preferences.field]);
  const scene = useMemo<ReferenceScene | null>(() => selected.status === 'ready' ? {
    id: 'observatory-state-replay', title: selected.definition.title, nodeCount: 128,
    values: selected.values,
    description: 'Fixed coordinate-index atlas. Proximity is a drawing choice, not physical location or recurrent connectivity. Derived values use the frozen reference fitted to this same capture.',
    provenance: `${state.sourceIdentity}. Reference: ${reference?.sourceIdentity ?? 'unavailable'}.`,
  } : null, [selected, state.sourceIdentity, reference?.sourceIdentity]);
  const usesModes = preferences.field === 'reconstruction' || preferences.field === 'residual';
  const fraction = state.fields?.centeredEnergy > 0 && selectedModes ? selectedModes.reconstructedEnergy / state.fields.centeredEnergy : null;
  return <section className="recorded-state-inspection" aria-label="Recorded state fields and spectrum">
    <div className="state-field-controls">
      <label>Surface field <select aria-label="Recorded surface field" value={preferences.field} onChange={event => {
        const field = event.target.value as ReferenceField;
        if (REFERENCE_FIELDS.includes(field)) onPreferences({ ...preferences, field });
      }}>{REFERENCE_FIELDS.map(field => <option key={field} value={field}>{referenceFieldDefinition(field)!.title}</option>)}</select></label>
      {usesModes && <label>Reconstruction modes <select aria-label="Reference reconstruction modes" value={preferences.modes} onChange={event => {
        const modes = Number(event.target.value);
        if (Number.isInteger(modes) && modes >= 0 && modes <= 3) onPreferences({ ...preferences, modes });
      }}><option value={3}>All three captured modes</option>{[0, 1, 2].map(index => <option key={index} value={index}>PC{index + 1}</option>)}</select></label>}
      <span className="subtle-tag">Same recorded row · {row}</span>
    </div>
    {selected.status === 'ready' && selected.definition.requiresReference && <p className="observatory-view-caption">Reference fitted to this entire capture. Reconstruction contains the selected centered components; it does not add the mean back. Residual is the remaining deviation.</p>}
    <div className="observatory-state-views">
      <div>{scene && selected.status === 'ready' ? <>
        <SurfaceView evidenceLabel={`Retained state row ${row}`} reference={scene} selected={node} onSelect={onNode} pose={pose} onPose={onPose} tableOnly={tableOnly} fixedScale={selected.definition.fixedScale} nonnegative={selected.definition.palette === 'magnitude'}/>
        <p className="observatory-view-caption">Relief and contours show the selected field on a fixed coordinate-index atlas, not physical anatomy or the full phase space.</p>
        {selected.outOfRangeCount > 0 && <p className="observatory-warning" role="status">{selected.outOfRangeCount} coordinates exceed the fixed display range. Exact values below remain unclipped.</p>}
      </> : <p role="status">{selected.status === 'unavailable' ? selected.reason : 'Surface unavailable.'} Raw signed values remain in the selected-row evidence.</p>}</div>
      <RecordedTrajectory points={points} total={total} selectedIndex={row} onSelect={onRow} projectionIndex={preferences.projection} onProjectionChange={projection => onPreferences({ ...preferences, projection })}/>
    </div>
    <section className="state-field-summary" aria-label="Selected coordinate evidence">
      <div><span>Raw activation · coordinate {node}</span><output>{exact(state.activations[node])}</output></div>
      <div><span>{selected.status === 'ready' ? selected.definition.title : 'Selected field'}</span><output>{selected.status === 'ready' ? exact(selected.values[node]) : 'Unavailable'}</output></div>
      {usesModes && <div><span>This row's squared deviation reconstructed</span><output>{fraction === null ? 'Unavailable' : `${(100 * fraction).toFixed(2)}%`}</output></div>}
    </section>
    <RecordedStateSpectrum reference={reference}/>
    <details className="observatory-state-note"><summary>Selected row: exact reference calculation and retained metrics</summary>
      <p>Field calculations use the original Float32 coordinates promoted to double precision and the retained mean/basis. They are distinct from rounded metrics and PC coordinates in the historical geometry file.</p>
      <dl>
        <div><dt>Recomputed mode scores · PC1/2/3</dt><dd>{state.fields?.scores.map(exact).join(' · ') ?? 'Unavailable'}</dd></div>
        <div><dt>Squared deviation from mean</dt><dd>{exact(state.fields?.centeredEnergy)}</dd></div>
        <div><dt>Reconstructed squared deviation · {wantedModes === '0,1,2' ? 'all three modes' : `PC${preferences.modes + 1}`}</dt><dd>{exact(selectedModes?.reconstructedEnergy)}</dd></div>
        <div><dt>Residual squared deviation · same modes</dt><dd>{exact(selectedModes?.residualEnergy)}</dd></div>
        <div><dt>Retained state RMS</dt><dd>{exact(state.stateRms)}</dd></div>
        <div><dt>Retained centered RMS</dt><dd>{exact(state.centeredRms)}</dd></div>
        <div><dt>Retained projected RMS · three modes</dt><dd>{exact(state.projectedRms)}</dd></div>
        <div><dt>Retained reconstruction RMSE · three modes</dt><dd>{exact(state.reconstructionRmse)}</dd></div>
      </dl>
      <p>Retained projection coordinates: {state.pc.map(exact).join(' · ')}. The row's reconstructed squared deviation is not the whole-capture variance share, a clock or a fill measurement.</p>
    </details>
    {scene && selected.status === 'ready' && <CoordinateInspector reference={scene} selected={node} onSelect={onNode} fixedScale={selected.definition.fixedScale} valueCaption={preferences.field === 'signedActivation' ? 'original signed values' : 'exact derived field values'} sourceNote="These values belong to this retained state row and its frozen capture reference. No live source or historical path is followed."/>}
  </section>;
}

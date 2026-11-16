#!/usr/bin/env python3
"""Read a stable laptop session prefix and derive a clearly separated spectral view.

No source writes or provider calls. Hash-checks the full captured segment chain;
this is not independent native numerical replay. The selected 300-step prefix
and one quoted journal are retained with the derivation and source identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from observe_sonar_exploration import read_regular, utc_now
from review_sonar_startup import capture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    assert not args.output.resolve().is_relative_to(args.session.resolve())
    manifest,state,raw,checkpoint=capture(args.session)
    assert state['step']>=300
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'manifest.capture.json').write_bytes(raw)
    (args.output/'checkpoint.capture.json').write_bytes(checkpoint)
    previous=None;frames={};hashes=[]
    for sequence in range(1,manifest['segmentCount']+1):
        path=args.session/'segments'/f'segment-{sequence:08d}.json'
        content=read_regular(path);link=json.loads(content)
        assert link['sequence']==sequence and link['previousSha256']==previous
        previous=hashlib.sha256(content).hexdigest();hashes.append({'file':path.name,'sha256':previous})
        for event in link['segment']['events']:
            if event['kind']['type']=='advanced':
                frame=event['kind']['data']
                if frame['step']<=300:
                    assert frame['step'] not in frames
                    frames[frame['step']]=frame
    assert previous==manifest['lastSegmentSha256']
    assert sorted(frames)==list(range(1,301))
    raw_frames=[frames[i] for i in range(1,301)]
    (args.output/'frames.json').write_text(json.dumps(raw_frames,allow_nan=False))
    x=np.array([f['state'] for f in raw_frames]);center=x.mean(axis=0)
    values,axes=np.linalg.eigh(np.cov(x,rowvar=False));order=np.argsort(values)[::-1];values=values[order];axes=axes[:,order]
    for j in range(axes.shape[1]):
        i=np.argmax(np.abs(axes[:,j]));axes[:,j]*=1 if axes[i,j]>=0 else -1
    projection=(x-center)@axes[:,:2]
    rows=[]
    for end in range(32,301):
        eig=np.maximum(np.linalg.eigvalsh(np.cov(x[end-32:end],rowvar=False))[::-1],0)
        sensory=np.array(frames[end]['sensory']['eigenvalues'])
        assert len(sensory)==32 and np.all(sensory>=0)
        rows.append({'step':end,'stateSpectrum':eig.tolist(),'sensorySpectrum':sensory.tolist(),
                     'stateTotal':float(eig.sum()),'sensoryTotal':float(sensory.sum()),
                     'fill':frames[end]['sensory']['fillPercent'],
                     'rms':float(np.sqrt(np.mean(x[end-1]**2)))})
    journals=list((args.session/'journals').glob('journal-150-*.json'));assert len(journals)==1
    jraw=read_regular(journals[0]);journal=json.loads(jraw);prompt=journal['pending']['prompt']
    (args.output/journals[0].name).write_bytes(jraw)
    # Inspect only the delivered numerical sections: prior prose can itself mention spectra.
    current=prompt.split('CURRENT OBSERVATION',1)[1].split('ACTIVE CONTROLS',1)[0]
    assert 'Separate sensory fill' in current and 'eigenvalues' not in current
    data={'source':'Gemma4 local scanner session, November 15, 2026; recorded numerical steps 1–300',
          'sessionId':manifest['sessionId'],'capturedAtUtc':utc_now(),
          'projection':projection.tolist(),'projectionShares':(values[:2]/values.sum()).tolist(),
          'samples':rows,'selectedJournal':{'file':journals[0].name,'sha256':hashlib.sha256(jraw).hexdigest(),
          'step':150,'currentObservation':'CURRENT OBSERVATION '+current.strip(),
          'body':journal['pending']['entry']['body']},
          'method':'Fixed PCA basis fitted to all 300 recurrent states; rolling spectra use the last 32 states, centered sample covariance. Sensory eigenvalues are native recorded measurements of the separate field. Neither plotted spectrum nor this PCA projection was supplied to the model as a plot.'}
    (args.output/'spectral-view.json').write_text(json.dumps(data,allow_nan=False))
    (args.output/'provenance.json').write_text(json.dumps({'sourceSession':str(args.session),'manifestSha256':hashlib.sha256(raw).hexdigest(),'checkpointFileSha256':manifest['checkpointSha256'],'segmentHashes':hashes,'derivation':'numpy.linalg.eigh/eigvalsh; centered sample covariance; fixed sign of each PCA axis','stateSamples':300,'rollingWindow':32,'modelCalls':False,'sourceWrites':False,'nativeReplayPerformed':False},indent=2))
    # Required identity checks: covariance trace equals variance sum, rotation preserves spectrum.
    cov=np.cov(x,rowvar=False)
    np.testing.assert_allclose(values.sum(),np.var(x,axis=0,ddof=1).sum(),rtol=1e-12)
    q,_=np.linalg.qr(np.arange(1024,dtype=float).reshape(32,32)+np.eye(32))
    np.testing.assert_allclose(np.linalg.eigvalsh(q.T@cov@q),np.linalg.eigvalsh(cov),atol=1e-12)
    assert np.isfinite(projection).all()
    print(json.dumps({'output':str(args.output),'frames':300,'rollingWindows':len(rows),'projectionShares':data['projectionShares'],'chainLinksChecked':len(hashes),'checksPassed':True}))

if __name__=='__main__':main()

"""Rebuild frozen canonical weights and projection on CPU; no LLM or live handles.

This supplementary reproducibility check does not rerun an evaluation response.
It records its own observation time and checks every retained trial's projection.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np


def digest(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def main():
    root=Path(sys.argv[1]);manifest=json.loads((root/'manifest.json').read_text())
    source=next(Path(p) for p in manifest['sources'] if p.endswith('/triple_reservoir_coreml.py'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['sources'][str(source)]
    sys.path.insert(0,str(source.parent))
    from triple_reservoir_coreml import build_canonical_reservoir
    np.random.seed(11);before=np.random.get_state()
    first,config=build_canonical_reservoir();after=np.random.get_state()
    assert before[0]==after[0] and np.array_equal(before[1],after[1]) and before[2:]==after[2:]
    np.random.seed(777);second,_=build_canonical_reservoir()
    arrays={name:value for name,value in vars(first).items() if isinstance(value,np.ndarray)}
    assert arrays
    for name,value in arrays.items():np.testing.assert_array_equal(value,getattr(second,name))
    protocol=json.loads((root/'protocol.json').read_text())
    model_config=json.loads((Path(protocol['model'])/'config.json').read_text())
    width=model_config['text_config']['hidden_size'];dim=protocol['settings']['input_dim']
    projection=(np.random.default_rng(137).standard_normal((width,dim))/np.sqrt(width)).astype(np.float32)
    projection_hash=digest(projection)
    assert projection_hash==json.loads((root/'calibration.json').read_text())['projection_sha256']
    checked=[]
    for spec in protocol['trials']:
        path=root/(spec['id']+'.json')
        if not path.exists():continue
        value=json.loads(path.read_text()).get('result')
        if value is not None:
            assert value['projection_sha256']==projection_hash
            checked.append(spec['id'])
    archive=root/'reconstructed-canonical-arrays.npz'
    if not archive.exists():
        np.savez_compressed(archive,projection=projection,**arrays);archive.chmod(0o400)
    receipt=dict(schema='contextual_numerical_receipt_v1',observed_unix=time.time(),
        source_sha256=manifest['sources'][str(source)],input_dim=config.input_dim,
        canonical_rebuilds_bit_identical=True,canonical_build_preserves_global_numpy_rng=True,
        arrays={name:dict(shape=value.shape,dtype=str(value.dtype),sha256=digest(value)) for name,value in arrays.items()},
        projection_sha256=projection_hash,checked_trial_projections=checked,
        scope='Reconstruction from frozen source and current verified dependencies; not per-trial instrumentation. No generation, state checkin or live handle call.')
    (root/'numerical-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(canonical_arrays=len(arrays),projection_verified=True,trials_checked=len(checked))))


if __name__=='__main__':main()

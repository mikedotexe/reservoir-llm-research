#!/usr/bin/env python3
"""One read-only libproc snapshot of the exact replaceable app executable only.

Does not signal, activate, launch, sample resources or inspect unrelated arguments.
The result is an observation, not permission to replace a still-running app.
"""
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
DESKTOP = HERE.parents[1]
class BSDInfo(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')] + [('comm', C.c_char*16),('name', C.c_char*32)] + [(n,C.c_uint32) for n in ('nfiles','pgid','jobc','tdev','tpgid')] + [('nice',C.c_int32),('start_seconds',C.c_uint64),('start_microseconds',C.c_uint64)]

def snapshot(expected):
    if sys.platform != 'darwin': raise ValueError('macOS libproc required')
    lib=C.CDLL('/usr/lib/libproc.dylib',use_errno=True)
    lib.proc_listpids.argtypes=[C.c_uint32,C.c_uint32,C.c_void_p,C.c_int];lib.proc_listpids.restype=C.c_int
    lib.proc_pidpath.argtypes=[C.c_int,C.c_void_p,C.c_uint32];lib.proc_pidpath.restype=C.c_int
    lib.proc_pidinfo.argtypes=[C.c_int,C.c_int,C.c_uint64,C.c_void_p,C.c_int];lib.proc_pidinfo.restype=C.c_int
    pids=(C.c_int*16384)();size=lib.proc_listpids(1,0,pids,C.sizeof(pids))
    if size<=0 or size>=C.sizeof(pids) or size%C.sizeof(C.c_int):raise ValueError('Incomplete PID enumeration')
    matches=[];unreadable=0
    for pid in pids[:size//C.sizeof(C.c_int)]:
        if pid<=0:continue
        path=C.create_string_buffer(4096)
        if lib.proc_pidpath(pid,path,len(path))<=0:unreadable+=1;continue
        if os.fsdecode(path.value)!=str(expected):continue
        info=BSDInfo()
        if lib.proc_pidinfo(pid,3,0,C.byref(info),C.sizeof(info))!=C.sizeof(info):raise ValueError('Selected process identity changed or unavailable')
        again=C.create_string_buffer(4096)
        if lib.proc_pidpath(pid,again,len(again))<=0 or again.value!=path.value:raise ValueError('Selected path changed during identity read')
        matches.append({'pid':pid,'uid':info.uid,'executablePath':str(expected),'startSeconds':str(info.start_seconds),'startMicroseconds':str(info.start_microseconds)})
    return {'matches':matches,'unreadablePidPaths':unreadable,'limitations':'One bounded snapshot, exact selected executable only; inaccessible/exited PIDs are not a global process-absence proof.'}

def main():
    expected=DESKTOP/'target/release/bundle/macos/Reservoir Scope Tauri Preview.app/Contents/MacOS/reservoir-scope-desktop'
    report={'schema':'reservoir-exact-app-process-observation-v1','observedAtUtc':datetime.now(timezone.utc).isoformat(),'expectedExecutable':str(expected),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actions':{'signals':False,'applicationActivation':False,'services':False},**snapshot(expected)}
    out=HERE/'prior-process-identity-01.json'
    with out.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'receipt':str(out),'matches':report['matches'],'unreadablePidPaths':report['unreadablePidPaths']}))
if __name__=='__main__':main()

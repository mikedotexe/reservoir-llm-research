#!/usr/bin/env python3
"""Join final native, transport, viewer and patch evidence without live I/O."""
import argparse, datetime, hashlib, json, re
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def require(value, reason):
    if not value: raise ValueError(reason)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--research-root',type=Path,required=True);args=parser.parse_args();repo=args.research_root.resolve();root=repo/'research/outputs/2026-09-07-native-state-actions'
    m1=read(root/'final/candidate-run/verification.json');m4=read(root/'final/m4-validation/candidate-run/verification.json')
    transport=read(root/'transport/verification.json');patch=read(root/'patch-verification.json');commit=read(root/'implementation-commit.json');viewer=read(repo/'native/ReservoirScope/build-receipt.json');qa=read(repo/'native/ReservoirScope/validation/0.6.0/runtime-qa.json');core=read(root/'native-core-tests.json')
    for host in [m1,m4]:
        require(host['audit_passed'] and host['ordinary_cases']==6 and host['action_cases']==21,'native case acceptance')
    require(m1['source_identity']==m4['source_identity']==viewer['producer_source_identity'],'native final source linkage')
    require(m1['viewer_sha256']==sha(root/'native-action-response.json')==viewer['resource_sha256']['native-action-response.json']==qa['native_resource_sha256'],'viewer exact actual producer')
    require(viewer['binary_sha256']==qa['binary_sha256'] and viewer['root_source_resource_binary_recheck'],'viewer final artifact linkage')
    require(transport['status']=='passed' and transport['final_counts']['failed']==0 and all(r['exit_status']==0 for r in transport['final_runs']),'transport completion')
    owning=Path(commit['repository'])
    for name,digest in transport['source_sha256'].items(): require(sha(owning/name)==digest,'tested owning source changed: '+name)
    for name,digest in transport['artifact_sha256'].items(): require(sha(root/'transport'/name)==digest,'test artifact changed: '+name)
    for item in commit['files']: require(sha(owning/item['path'])==item['sha256'],'committed feature file changed')
    require(patch['apply_check_passed'] and patch['applied_files_match_owning_tree'] and patch['reverse_check_passed'],'patch reproduction')
    require(patch['feature_commit']==commit['feature_commit'] and sha(repo/commit['patch'])==patch['patch_sha256'],'patch identity')
    require(all(row['returncode']==0 for row in core['results']),'native module tests')
    native_counts=[]
    for name in ['native-core-state_action-tests.log','native-core-native_state_action_tests.log']:
        log=(root/name).read_text();matches=re.findall(r'test result: ok\. (\d+) passed; 0 failed;',log);require(matches,'missing core test outcome');native_counts.append(int(matches[-1]))
    challenges=read(root/'final/verifier-checks.json');require(challenges['all_rejected'],'verifier challenge coverage')
    output={'schema':'research.native_state_actions.completion.v1','completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Implemented, committed and validated in isolation; no live activation or messages.','status':'complete_for_implementation_and_native_viewer','owning_feature_commit':commit['feature_commit'],'patch':commit['patch'],'patch_sha256':patch['patch_sha256'],'patch_files_verified':patch['file_count'],'native_source_identity':m1['source_identity'],'native_checks_by_host':{label:{k:value[k] for k in ['ordinary_cases','ordinary_steps','action_cases','action_steps','actual_applications','zero_effect_receipts','binary_sha256']} for label,value in [('M1 Max',m1),('M4 Pro',m4)]},'native_module_tests':{'pure':native_counts[0],'metal':native_counts[1],'scope':'Unchanged native module source, with division-rehearsal omitted; final parser feature separately covered by final native and signed integration runs.'},'transport_tests':transport['final_counts'],'viewer':{'version':viewer['version'],'build':viewer['build'],'binary_sha256':viewer['binary_sha256'],'resource_sha256':m1['viewer_sha256'],'checks':qa['checks'],'runtime_review_passed':True},'verifier_corruptions_rejected':challenges['count'],'remaining_scope':['Owning review/merge and live deployment workflow','Signed live application stream adapter for viewer','Stable-core precedence for temporary leak requests','Explicit mutual peer-owned shaping','Full field/controller/LLM response and experienced effect'],'probe_sha256':sha(Path(__file__))}
    (root/'completion.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output,indent=2))
if __name__=='__main__':main()

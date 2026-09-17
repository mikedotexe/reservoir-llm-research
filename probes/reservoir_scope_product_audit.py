"""Read-only product audit of bundled Reservoir Scope examples. No model or live-source calls."""
import argparse,json,math,hashlib
from pathlib import Path
def audit(app):
    root=app/"Contents/Resources"
    read=lambda name:json.loads((root/name).read_bytes())
    result={"schema":"reservoir_scope_product_audit_v1","package_identity_sha256":hashlib.sha256((root/"release-identity.json").read_bytes()).hexdigest(),"example_count":len(read("examples-index.json")),"scripted":[],"model_components":[]}
    for stage in range(1,9):
        r=read(f"example-component-{stage}.json");right=r["right"];left=r.get("left");frames=right["frames"]
        delta=[] if left is None else [math.sqrt(sum((x-y)**2 for x,y in zip(a["state"],b["state"]))/32) for a,b in zip(left["frames"],frames)]
        row={"stage":chr(64+stage),"paired":left is not None,"journals":len(right["journals"]),"actions":[{"step":a["observedStep"],"choice":a.get("chosenAction"),"application_step":a.get("applicationStep")} for a in right["actions"]],"first_state_difference_over_1e_14":next((i+1 for i,d in enumerate(delta) if d>1e-14),None),"peak_state_rms_difference":max(delta,default=0)}
        if stage==6:row.update(second_prompt_contains_prior_journal=right["actions"][1].get("memoryText")==right["journals"][0]["text"],replies_equal=all(a.get("rawReply")==b.get("rawReply") for a,b in zip(left["actions"],right["actions"])))
        if stage==8:row.update(final_fill=[left["frames"][-1]["fillPercent"],frames[-1]["fillPercent"]],final_retention=[left["frames"][-1]["retentionUsed"],frames[-1]["retentionUsed"]])
        result["scripted"].append(row)
    for stage in range(4,9):
        r=read(f"example-model-{stage}.json")
        result["model_components"].append({"stage":chr(64+stage),"paired":r.get("left") is not None,"choices":[a.get("chosenAction") for a in r["right"]["actions"]]})
    r=read("example-model-observation.json")
    result["observation"]={"steps":r["specification"]["steps"],"maximum_abs_state_over_run":max(abs(v) for f in r["right"]["frames"] for v in f["state"]),"maximum_abs_state_at_journal":[{"step":a["observedStep"],"value":max(abs(v) for v in r["right"]["frames"][a["observedStep"]-1]["state"])} for a in r["right"]["actions"]]}
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("app",type=Path);a=p.parse_args();print(json.dumps(audit(a.app),indent=2))

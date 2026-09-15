//! Research entry point only. Compiled with byte-identical copied native modules.
//! No runtime, sensory bus, sockets, journals, databases or process control.
mod buffer_pool;
mod gpu;
mod esn;

use anyhow::{bail, Result};
use esn::{ESN, EsnSnapshotV2, EsnStepTraceV1};
use gpu::Gpu;
use serde_json::{json, Value};
use std::{fs, path::Path};

fn write(out: &Path, name: &str, value: &impl serde::Serialize) -> Result<()> {
    fs::write(out.join(name), serde_json::to_vec(value)?)?;
    Ok(())
}
fn input(t: usize) -> Vec<f32> {
    (0..66).map(|i| 0.15_f32 * (((t * 7 + i * 3) as f32) * 0.071_f32).sin()).collect()
}
fn maxabs(a: &[f32], b: &[f32]) -> f64 {
    a.iter().zip(b).map(|(x,y)| (*x as f64-*y as f64).abs()).fold(0., f64::max)
}
fn l2(a: &[f32], b: &[f32]) -> f64 {
    a.iter().zip(b).map(|(x,y)| (*x as f64-*y as f64).powi(2)).sum::<f64>().sqrt()
}
fn obs(e: &ESN) -> Value {
    json!({"geom_radius":e.get_geom_radius(), "geom_baseline":e.get_geom_baseline(),
        "esn_state_covariance_eig1":e.get_eig(), "esn_state_covariance_eig_baseline":e.get_baseline(),
        "adaptive_leak":e.get_leak(), "effective_leak_last_step":e.last_step_trace().leak,
        "rls_lambda":e.get_lambda(), "saturated_coordinates":e.x.iter().filter(|x| x.abs()==1.).count()})
}
fn clean_snapshot(s: &EsnSnapshotV2, omit_rng: bool) -> Result<Value> {
    let mut v=serde_json::to_value(s)?;
    v["spectral"].as_object_mut().unwrap().remove("last_profile");
    if omit_rng { v.as_object_mut().unwrap().remove("rng_state"); }
    Ok(v)
}
fn value_error(a: &Value, b: &Value) -> f64 {
    match (a,b) {
        (Value::Number(x),Value::Number(y)) => (x.as_f64().unwrap()-y.as_f64().unwrap()).abs(),
        (Value::Array(x),Value::Array(y)) if x.len()==y.len() => x.iter().zip(y).map(|(u,v)|value_error(u,v)).fold(0.,f64::max),
        (Value::Object(x),Value::Object(y)) if x.len()==y.len() => x.iter().map(|(k,v)| y.get(k).map_or(f64::INFINITY,|w|value_error(v,w))).fold(0.,f64::max),
        _ if a==b => 0.,
        _ => f64::INFINITY,
    }
}
struct Fixture {
    start: usize,
    snapshot: EsnSnapshotV2,
    forcing: Vec<EsnStepTraceV1>,
    control: Vec<Vec<f32>>,
}

fn parity(gpu: &Gpu, p: &Value, out: &Path) -> Result<(Vec<Value>,Vec<Fixture>)> {
    let mut results=vec![];
    let mut fixtures=vec![];
    let horizon=p["horizon_steps"].as_u64().unwrap() as usize;
    for mode in p["parity_modes"].as_array().unwrap() {
        let mode=mode.as_str().unwrap();
        for start in p["checkpoint_successful_boundaries"].as_array().unwrap() {
            let start=start.as_u64().unwrap() as usize;
            let mut rng=fastrand::Rng::with_seed(p["constructor_seed"].as_u64().unwrap());
            let mut parent=ESN::new(128,66,0.25,0.15,0.95,0.35,0.999,gpu,&mut rng)?;
            parent.set_profiling_enabled(mode=="synchronous_profile");
            for t in 0..start { parent.step(&input(t))?; }
            let snap=parent.snapshot_v2()?;
            let bytes=serde_json::to_vec(&snap)?;
            let restored_snapshot:EsnSnapshotV2=serde_json::from_slice(&bytes)?;
            fs::write(out.join(format!("checkpoint-{mode}-{start}.json")),bytes)?;
            let mut restored=ESN::from_snapshot_v2(&restored_snapshot,gpu)?;
            let mut shadow=ESN::from_snapshot_v2(&restored_snapshot,gpu)?;
            let mut duplicate=ESN::from_snapshot_v2(&restored_snapshot,gpu)?;
            let mut paths=vec![vec![parent.x.clone()],vec![restored.x.clone()],vec![shadow.x.clone()],vec![duplicate.x.clone()]];
            let mut observations=vec![vec![obs(&parent)],vec![obs(&restored)],vec![obs(&shadow)],vec![obs(&duplicate)]];
            let mut forcing=vec![];
            let mut state_error=0_f64;
            let mut shadow_error=0_f64;
            let mut duplicate_error=0_f64;
            let mut noise_error=0_f64;
            let mut leak_error=0_f64;
            let mut covariance_error=0_f64;
            let mut exact= true;
            for t in start..start+horizon {
                let u=input(t);
                parent.step(&u)?;
                let trace=parent.last_step_trace().clone();
                if trace.noise.len()!=128 { bail!("realized noise unavailable") }
                restored.step(&u)?;
                shadow.step_shadow(&u,&vec![0.;128],&trace.noise,trace.leak)?;
                duplicate.step_shadow(&u,&vec![0.;128],&trace.noise,trace.leak)?;
                state_error=state_error.max(maxabs(&parent.x,&restored.x));
                shadow_error=shadow_error.max(maxabs(&parent.x,&shadow.x));
                duplicate_error=duplicate_error.max(maxabs(&shadow.x,&duplicate.x));
                exact &= parent.x==restored.x && parent.x==shadow.x && shadow.x==duplicate.x;
                noise_error=noise_error.max(maxabs(&trace.noise,&restored.last_step_trace().noise));
                leak_error=leak_error.max((trace.leak as f64-restored.last_step_trace().leak as f64).abs());
                for (index,e) in [&parent,&restored,&shadow,&duplicate].iter().enumerate() {
                    paths[index].push(e.x.clone()); observations[index].push(obs(e));
                }
                forcing.push(trace);
            }
            let final_parent=parent.snapshot_v2()?;
            let final_restored=restored.snapshot_v2()?;
            let final_shadow=shadow.snapshot_v2()?;
            let final_duplicate=duplicate.snapshot_v2()?;
            covariance_error=covariance_error.max(maxabs(&final_parent.spectral.covariance,&final_restored.spectral.covariance));
            let snapshot_error=value_error(&clean_snapshot(&final_parent,false)?,&clean_snapshot(&final_restored,false)?);
            let shadow_snapshot_error=value_error(&clean_snapshot(&final_parent,true)?,&clean_snapshot(&final_shadow,true)?);
            let duplicate_snapshot_error=value_error(&clean_snapshot(&final_shadow,false)?,&clean_snapshot(&final_duplicate,false)?);
            let tolerance=p["parity"]["state_max_abs_tolerance"].as_f64().unwrap();
            let passed=state_error<=tolerance && shadow_error<=tolerance && duplicate_error==0.
                && noise_error==0. && leak_error==0. && snapshot_error<=tolerance
                && shadow_snapshot_error<=tolerance && duplicate_snapshot_error==0.;
            let record=json!({"mode":mode,"start_boundary":start,"horizon_steps":horizon,
                "ordinary_restored_state_max_abs":state_error,"ordinary_shadow_state_max_abs":shadow_error,
                "shadow_duplicate_state_max_abs":duplicate_error,"all_state_paths_bit_identical":exact,
                "realized_noise_max_abs":noise_error,"effective_leak_max_abs":leak_error,
                "final_covariance_max_abs":covariance_error,"final_snapshot_numeric_max_abs":snapshot_error,
                "final_shadow_snapshot_numeric_max_abs_excluding_rng":shadow_snapshot_error,
                "final_duplicate_snapshot_numeric_max_abs":duplicate_snapshot_error,"passed":passed});
            write(out,&format!("parity-paths-{mode}-{start}.json"),&json!({"order":["ordinary","restored","shadow","shadow_duplicate"],"paths":paths,"observables":observations,"forcing":forcing,
                "inputs":(start..start+horizon).map(input).collect::<Vec<_>>(),"external_recurrence":vec![0.;128]}))?;
            write(out,&format!("final-checkpoints-{mode}-{start}.json"),&json!({"ordinary":final_parent,"restored":final_restored,"shadow":final_shadow,"shadow_duplicate":final_duplicate}))?;
            println!("parity {mode} start {start}: passed={passed}; native restore={state_error}; shadow={shadow_error}");
            results.push(record);
            write(out,"parity-results.json",&results)?;
            if mode=="synchronous_profile" {
                fixtures.push(Fixture{start,snapshot:restored_snapshot,forcing,control:paths.remove(0)});
            }
        }
    }
    Ok((results,fixtures))
}

fn edit(e: &mut ESN, gpu: &Gpu, direction: &[f32], dose:f32, boundary:usize) -> Result<Value> {
    let mut snapshot=e.snapshot_v2()?;
    let before=snapshot.state.clone();
    let requested:Vec<f32>=direction.iter().map(|x|dose*x).collect();
    let mut clipped=0;
    for ((x,b),d) in snapshot.state.iter_mut().zip(&before).zip(&requested) {
        let raw=*b+*d;
        *x=raw.clamp(-1.,1.);
        clipped+=usize::from(raw!=*x);
    }
    let actual:Vec<f32>=snapshot.state.iter().zip(&before).map(|(a,b)|a-b).collect();
    snapshot.geom_radius=(snapshot.state.iter().map(|v|v*v).sum::<f32>()/128_f32).sqrt();
    let receipt=json!({"boundary":boundary,"requested_signed_l2":dose,"actual_l2":l2(&snapshot.state,&before),
        "clipped_coordinates":clipped,"rounding_and_clipping_delta_l2":l2(&actual,&requested),
        "before":before,"after":snapshot.state,"actual_delta":actual,"geom_radius":snapshot.geom_radius,
        "geom_baseline_preserved":snapshot.geom_baseline});
    *e=ESN::from_snapshot_v2(&snapshot,gpu)?;
    Ok(receipt)
}
fn unit(mut a:Vec<f32>)->Vec<f32> {
    let n=a.iter().map(|x|(*x as f64).powi(2)).sum::<f64>().sqrt();
    assert!(n>0. && n.is_finite());
    for x in &mut a { *x=(*x as f64/n) as f32; }
    a
}
fn response(gpu:&Gpu,p:&Value,out:&Path,f:&Fixture,direction:&[f32],name:&str,dose:f32,sequence:bool)->Result<Value> {
    let mut e=ESN::from_snapshot_v2(&f.snapshot,gpu)?;
    let id=format!("s{}-{name}-{}-{dose:+.4}",f.start,if sequence{"sequence"}else{"once"});
    let mut edits=vec![edit(&mut e,gpu,direction,dose,0)?];
    let mut path=vec![e.x.clone()];
    let mut observations=vec![obs(&e)];
    for (offset,trace) in f.forcing.iter().enumerate() {
        e.step_shadow(&input(f.start+offset),&vec![0.;128],&trace.noise,trace.leak)?;
        if sequence && offset<7 { edits.push(edit(&mut e,gpu,direction,dose,offset+1)?); }
        path.push(e.x.clone()); observations.push(obs(&e));
    }
    let separation:Vec<f64>=path.iter().zip(&f.control).map(|(a,b)|l2(a,b)).collect();
    let last_edit=if sequence{7}else{0};
    let reference=separation[last_edit];
    let threshold=reference*p["return_threshold_fraction"].as_f64().unwrap();
    let dwell=p["return_dwell_boundaries"].as_u64().unwrap() as usize;
    let returned=(last_edit+1..=separation.len()-dwell).find(|i|separation[*i..*i+dwell].iter().all(|d|*d<=threshold));
    let final_snapshot=e.snapshot_v2()?;
    let record=json!({"id":id,"start_boundary":f.start,"direction":name,"sequence":sequence,"signed_l2_dose":dose,
        "edit_count":edits.len(),"requested_cumulative_l2_budget":dose.abs() as f64*edits.len() as f64,
        "reference_boundary":last_edit,"reference_l2":reference,"peak_l2":separation.iter().copied().fold(0.,f64::max),
        "peak_gain_over_reference":separation.iter().copied().fold(0.,f64::max)/reference,
        "final_separation_l2":separation.last(),"return_threshold_l2":threshold,"return_boundary":returned,
        "any_observed_saturation":observations.iter().any(|v|v["saturated_coordinates"].as_u64().unwrap()>0),
        "initial_edit_l2":edits[0]["actual_l2"],"separation_l2":separation});
    write(out,&format!("response-{id}.json"),&json!({"summary":record,"direction_vector":direction,"states":path,
        "observables":observations,"edits":edits,"final_snapshot":final_snapshot}))?;
    Ok(record)
}
fn leak_checks(gpu:&Gpu,p:&Value,out:&Path,f:&Fixture)->Result<Vec<Value>> {
    let mut results=vec![];
    for c in p["leak_override_checks"]["cases"].as_array().unwrap() {
        let id=c["id"].as_str().unwrap();
        let leak=c["leak"].as_f64().unwrap() as f32;
        let duration=c["duration"].as_u64().unwrap() as u32;
        let cancel=c["cancel_after"].as_u64().map(|v|v as usize);
        let release=cancel.unwrap_or(duration.clamp(1,12) as usize);
        let mut control=ESN::from_snapshot_v2(&f.snapshot,gpu)?;
        let mut modified=ESN::from_snapshot_v2(&f.snapshot,gpu)?;
        modified.set_leak_override(leak,duration,id.to_string());
        let mut records=vec![];
        let mut passed=true;
        let mut control_path=vec![control.x.clone()];
        let mut modified_path=vec![modified.x.clone()];
        for t in 0..16 {
            if cancel==Some(t) { modified.clear_leak_override(); }
            let before_status=modified.leak_override_status();
            let mut cleared=if t==release {
                let s=modified.snapshot_v2()?;
                let mut e=ESN::from_snapshot_v2(&s,gpu)?;
                e.clear_leak_override(); Some(e)
            } else {None};
            let u=input(f.start+t);
            control.step(&u)?; modified.step(&u)?;
            let actual=modified.last_step_trace().leak;
            let expected=if t<release {Some(leak.clamp(0.2,0.9))}else{None};
            let noise_error=maxabs(&control.last_step_trace().noise,&modified.last_step_trace().noise);
            let remaining=modified.leak_override_status().map(|v|v.remaining_ticks);
            let expected_remaining=if t+1<release {Some(duration.clamp(1,12)-(t+1) as u32)}else{None};
            let release_error=if let Some(e)=cleared.as_mut() {
                e.step(&u)?; Some(maxabs(&modified.x,&e.x))
            }else{None};
            // The status on the last pre-cancel step still carries the unspent request.
            let expected_remaining=if cancel==Some(t+1) {Some(duration.clamp(1,12)-(t+1) as u32)}else{expected_remaining};
            let tick_pass=expected.is_none_or(|x|actual==x) && remaining==expected_remaining
                && noise_error==0. && release_error.is_none_or(|x|x==0.);
            passed &= tick_pass;
            records.push(json!({"offset":t,"before_status":before_status,"actual_effective_leak":actual,
                "expected_override_leak":expected,"status_remaining":remaining,"expected_remaining":expected_remaining,
                "realized_noise_control_max_abs":noise_error,"released_vs_cleared_state_max_abs":release_error,"passed":tick_pass}));
            control_path.push(control.x.clone()); modified_path.push(modified.x.clone());
        }
        let separation:Vec<f64>=modified_path.iter().zip(&control_path).map(|(a,b)|l2(a,b)).collect();
        let record=json!({"id":id,"passed":passed,"release_before_offset":release,"separation_l2":separation,
            "scope":"ordinary native adaptation with same ordinary RNG/noise; effective leak intentionally differs during override"});
        write(out,&format!("leak-{id}.json"),&json!({"summary":record,"ticks":records,"control":control_path,"modified":modified_path}))?;
        results.push(record);
    }
    Ok(results)
}
fn main()->Result<()> {
    let args:Vec<_>=std::env::args().collect();
    if args.len()!=3 {bail!("usage: rehearsal PROTOCOL OUTPUT")}
    let p:Value=serde_json::from_slice(&fs::read(&args[1])?)?;
    let out=Path::new(&args[2]);
    let gpu=Gpu::new()?;
    let device=gpu.dev.name().to_string();
    let (parity_results,fixtures)=parity(&gpu,&p,out)?;
    let synchronous_pass=parity_results.iter().filter(|r|r["mode"]=="synchronous_profile").all(|r|r["passed"]==true);
    let mut responses=vec![];
    let mut leaks=vec![];
    if synchronous_pass {
        let mut rng=fastrand::Rng::with_seed(p["direction_seed"].as_u64().unwrap());
        let random=unit((0..128).map(|_|rng.f32()*2.-1.).collect());
        let mut coordinate=vec![0.;128]; coordinate[0]=1.;
        for f in &fixtures {
            let spectral=unit(f.snapshot.spectral.eigenvector.clone());
            for (name,direction) in [("coordinate_0",&coordinate),("seeded_uniform_unit_vector",&random),("checkpoint_spectral_eigenvector_unit",&spectral)] {
                for dose in p["signed_l2_doses"].as_array().unwrap() {
                    responses.push(response(&gpu,&p,out,f,direction,name,dose.as_f64().unwrap() as f32,false)?);
                }
            }
            for dose in p["sequence"]["signed_l2_doses"].as_array().unwrap() {
                responses.push(response(&gpu,&p,out,f,&coordinate,"coordinate_0",dose.as_f64().unwrap() as f32,true)?);
            }
            println!("paired response start {} complete",f.start);
        }
        leaks=leak_checks(&gpu,&p,out,&fixtures[0])?;
    }
    let once:Vec<_>=responses.iter().filter(|r|r["sequence"]==false).collect();
    let sequence:Vec<_>=responses.iter().filter(|r|r["sequence"]==true).collect();
    let summary=json!({"parity_cases":parity_results.len(),"parity_passed":parity_results.iter().filter(|r|r["passed"]==true).count(),
        "synchronous_intervention_gate_passed":synchronous_pass,"one_shot_runs":once.len(),
        "one_shot_returned":once.iter().filter(|r|!r["return_boundary"].is_null()).count(),
        "sequence_runs":sequence.len(),"sequence_returned_after_release":sequence.iter().filter(|r|!r["return_boundary"].is_null()).count(),
        "leak_override_cases":leaks.len(),"leak_override_passed":leaks.iter().filter(|r|r["passed"]==true).count()});
    write(out,"results.json",&json!({"schema":"research.native_shaping_rehearsal.result.v1","subject":p["subject"],
        "not_replayed":p["not_replayed"],"metal_device":device,"summary":summary,"parity":parity_results,"responses":responses,"leak_override":leaks}))?;
    println!("{}",serde_json::to_string_pretty(&summary)?);
    Ok(())
}

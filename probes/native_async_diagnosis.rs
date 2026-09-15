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
const BUILD_VARIANT: &str = env!("RESEARCH_BUILD_VARIANT");
const BUILD_SOURCE_SHA256: &str = env!("RESEARCH_SOURCE_SHA256");

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
            let fixture=Path::new(p["checkpoint_input_dir"].as_str().unwrap()).join(format!("checkpoint-asynchronous_default-{start}.json"));
            let mut parent=if p["fresh_construct"]==true {
                let mut rng=fastrand::Rng::with_seed(p["constructor_seed"].as_u64().unwrap());
                let mut e=ESN::new(128,66,0.25,0.15,0.95,0.35,0.999,gpu,&mut rng)?;
                e.set_profiling_enabled(false);
                e.set_async_measurement_enabled(mode=="asynchronous_measured");
                for t in 0..start {e.step(&input(t))?;}
                e
            } else {
                let common:EsnSnapshotV2=serde_json::from_slice(&fs::read(fixture)?)?;
                ESN::from_snapshot_v2(&common,gpu)?
            };
            parent.set_profiling_enabled(false);
            parent.set_async_measurement_enabled(mode=="asynchronous_measured");
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
            let mut copy_forcing:Vec<Vec<EsnStepTraceV1>>=vec![vec![],vec![],vec![],vec![]];
            let mut state_error=0_f64;
            let mut shadow_error=0_f64;
            let mut duplicate_error=0_f64;
            let mut noise_error=0_f64;
            let mut leak_error=0_f64;
            let mut covariance_error=0_f64;
            let mut exact= true;
            let mut profiles:Vec<Vec<Value>>=vec![vec![],vec![],vec![],vec![]];
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
                    profiles[index].push(serde_json::to_value(e.profile_snapshot())?);
                    copy_forcing[index].push(e.last_step_trace().clone());
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
            let passed=clean_snapshot(&final_parent,false)?==clean_snapshot(&final_restored,false)?
                && clean_snapshot(&final_parent,true)?==clean_snapshot(&final_shadow,true)?
                && clean_snapshot(&final_shadow,false)?==clean_snapshot(&final_duplicate,false)?
                && exact && state_error<=tolerance && shadow_error<=tolerance && duplicate_error==0.
                && noise_error==0. && leak_error==0. && snapshot_error<=tolerance
                && shadow_snapshot_error<=tolerance && duplicate_snapshot_error==0.;
            let record=json!({"mode":mode,"start_boundary":start,"horizon_steps":horizon,
                "ordinary_restored_state_max_abs":state_error,"ordinary_shadow_state_max_abs":shadow_error,
                "shadow_duplicate_state_max_abs":duplicate_error,"all_state_paths_bit_identical":exact,
                "realized_noise_max_abs":noise_error,"effective_leak_max_abs":leak_error,
                "final_covariance_max_abs":covariance_error,"final_snapshot_numeric_max_abs":snapshot_error,
                "final_shadow_snapshot_numeric_max_abs_excluding_rng":shadow_snapshot_error,
                "final_duplicate_snapshot_numeric_max_abs":duplicate_snapshot_error,
                "ordinary_restored_final_snapshot_exact":clean_snapshot(&final_parent,false)?==clean_snapshot(&final_restored,false)?,
                "ordinary_shadow_final_snapshot_exact_excluding_rng":clean_snapshot(&final_parent,true)?==clean_snapshot(&final_shadow,true)?,
                "shadow_duplicate_final_snapshot_exact":clean_snapshot(&final_shadow,false)?==clean_snapshot(&final_duplicate,false)?,
                "async_submissions":profiles.iter().flatten().filter(|v|v["async_rank1_submitted"]==true).count(),
                "boundaries_with_pending_rank1":profiles.iter().flatten().filter(|v|v["pending_rank1_depth"].as_u64().unwrap()>0).count(),
                "max_pending_depth":profiles.iter().flatten().map(|v|v["pending_rank1_depth"].as_u64().unwrap()).max(),
                "passed":passed});
            write(out,&format!("parity-paths-{mode}-{start}.json"),&json!({"order":["ordinary","restored","shadow","shadow_duplicate"],"paths":paths,"observables":observations,"profiles":profiles,"forcing":forcing,"copy_forcing":copy_forcing,
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

fn rho_snapshot(s:&EsnSnapshotV2)->Result<Value> {
    let mut value=clean_snapshot(s,false)?;
    value["spectral"].as_object_mut().unwrap().remove("profiling_enabled");
    value["spectral"].as_object_mut().unwrap().remove("async_measurement_enabled");
    Ok(value)
}

fn rho_qualification(gpu:&Gpu,p:&Value,out:&Path)->Result<Vec<Value>> {
    let mut cases=vec![];
    let horizon=p["horizon_steps"].as_u64().unwrap() as usize;
    for start in p["checkpoint_successful_boundaries"].as_array().unwrap() {
        let start=start.as_u64().unwrap() as usize;
        let path=Path::new(p["checkpoint_input_dir"].as_str().unwrap()).join(format!("checkpoint-asynchronous_default-{start}.json"));
        let common:EsnSnapshotV2=serde_json::from_slice(&fs::read(path)?)?;
        for schedule in ["fixed","alternating"] {
            let mut paths=vec![];
            let mut observables=vec![];
            let mut traces=vec![];
            let mut profiles=vec![];
            let mut finals=vec![];
            let mut rho_values=vec![];
            // Complete each whole asynchronous trajectory before the waited
            // synchronous reference can run on the shared queue.
            for execution in ["async_a","async_b","synchronous_reference"] {
                let mut e=ESN::from_snapshot_v2(&common,gpu)?;
                e.set_profiling_enabled(execution=="synchronous_reference");
                e.set_async_measurement_enabled(p["measurement"]==true);
                let mut states=vec![e.x.clone()];
                let mut observations=vec![obs(&e)];
                let mut forcing=vec![];
                let mut prof=vec![];
                let mut rhos=vec![];
                for offset in 0..horizon {
                    let rho=if schedule=="fixed" {common.spectral.rho} else if offset%2==0 {0.82_f32} else {0.999_f32};
                    e.set_rho_direct(rho);
                    e.step(&input(start+offset))?;
                    states.push(e.x.clone());observations.push(obs(&e));forcing.push(e.last_step_trace().clone());
                    prof.push(serde_json::to_value(e.profile_snapshot())?);rhos.push(rho);
                }
                // The only terminal synchronization before inspecting covariance.
                finals.push(e.snapshot_v2()?);
                paths.push(states);observables.push(observations);traces.push(forcing);profiles.push(prof);rho_values.push(rhos);
            }
            let state_ab=paths[0].iter().zip(&paths[1]).map(|(a,b)|maxabs(a,b)).fold(0.,f64::max);
            let state_as=paths[0].iter().zip(&paths[2]).map(|(a,b)|maxabs(a,b)).fold(0.,f64::max);
            let state_bs=paths[1].iter().zip(&paths[2]).map(|(a,b)|maxabs(a,b)).fold(0.,f64::max);
            let snapshot_ab=value_error(&rho_snapshot(&finals[0])?,&rho_snapshot(&finals[1])?);
            let snapshot_as=value_error(&rho_snapshot(&finals[0])?,&rho_snapshot(&finals[2])?);
            let snapshot_bs=value_error(&rho_snapshot(&finals[1])?,&rho_snapshot(&finals[2])?);
            let mut noise_error=0_f64;let mut leak_error=0_f64;
            for index in [1,2] {
                for (a,b) in traces[0].iter().zip(&traces[index]) {
                    noise_error=noise_error.max(maxabs(&a.noise,&b.noise));
                    leak_error=leak_error.max((a.leak as f64-b.leak as f64).abs());
                }
            }
            let exact=paths[0]==paths[1] && paths[0]==paths[2]
                && rho_snapshot(&finals[0])?==rho_snapshot(&finals[1])?
                && rho_snapshot(&finals[0])?==rho_snapshot(&finals[2])?;
            let record=json!({"start_boundary":start,"schedule":schedule,"horizon_steps":horizon,
                "state_async_a_b_max_abs":state_ab,"state_async_a_sync_max_abs":state_as,"state_async_b_sync_max_abs":state_bs,
                "snapshot_async_a_b_max_abs":snapshot_ab,"snapshot_async_a_sync_max_abs":snapshot_as,"snapshot_async_b_sync_max_abs":snapshot_bs,
                "all_states_and_numerical_snapshots_exact":exact,"realized_noise_max_abs":noise_error,"effective_leak_max_abs":leak_error,
                "async_submissions":profiles[..2].iter().flatten().filter(|v|v["async_rank1_submitted"]==true).count(),
                "boundaries_with_pending_rank1":profiles[..2].iter().flatten().filter(|v|v["pending_rank1_depth"].as_u64().unwrap()>0).count(),
                "max_pending_depth":profiles[..2].iter().flatten().map(|v|v["pending_rank1_depth"].as_u64().unwrap()).max(),
                "passed":exact && noise_error==0. && leak_error==0.});
            write(out,&format!("rho-paths-{schedule}-{start}.json"),&json!({"order":["async_a","async_b","synchronous_reference"],
                "paths":paths,"observables":observables,"copy_forcing":traces,"profiles":profiles,"rho_schedule":rho_values,
                "inputs":(start..start+horizon).map(input).collect::<Vec<_>>()}))?;
            write(out,&format!("rho-final-checkpoints-{schedule}-{start}.json"),&json!({"async_a":finals[0],"async_b":finals[1],"synchronous_reference":finals[2]}))?;
            cases.push(record);
        }
    }
    write(out,"rho-results.json",&cases)?;
    Ok(cases)
}

fn main()->Result<()> {
    let args:Vec<_>=std::env::args().collect();
    if args.len()==2 && args[1]=="--identity" {
        println!("{}",json!({"compiled_variant":BUILD_VARIANT,"compiled_esn_sha256":BUILD_SOURCE_SHA256}));
        return Ok(());
    }
    if args.len()!=3 {bail!("usage: native-async-diagnosis PROTOCOL OUTPUT")}
    let p:Value=serde_json::from_slice(&fs::read(&args[1])?)?;
    if p["variant"].as_str()!=Some(BUILD_VARIANT) {bail!("compiled variant differs from run protocol")}
    let out=Path::new(&args[2]);
    let gpu=Gpu::new()?;
    let device=gpu.dev.name().to_string();
    let (cases,_)=parity(&gpu,&p,out)?;
    let rho_cases=if p["stage"]=="qualification" {rho_qualification(&gpu,&p,out)?}else{vec![]};
    let summary=json!({"cases":cases.len(),"passed":cases.iter().filter(|v|v["passed"]==true).count(),
        "all_state_paths_bit_identical":cases.iter().all(|v|v["all_state_paths_bit_identical"]==true),
        "max_pending_depth":cases.iter().map(|v|v["max_pending_depth"].as_u64().unwrap()).max(),
        "boundaries_with_pending_rank1":cases.iter().map(|v|v["boundaries_with_pending_rank1"].as_u64().unwrap()).sum::<u64>(),
        "async_submissions":cases.iter().map(|v|v["async_submissions"].as_u64().unwrap()).sum::<u64>()});
    let mut summary=summary;
    summary["rho_cases"]=json!(rho_cases.len());
    summary["rho_passed"]=json!(rho_cases.iter().filter(|v|v["passed"]==true).count());
    write(out,"results.json",&json!({"schema":"research.native_async_diagnosis.result.v1","metal_device":device,
        "compiled_variant":BUILD_VARIANT,"compiled_esn_sha256":BUILD_SOURCE_SHA256,
        "variant":p["variant"],"repeat":p["repeat"],"measurement":p["measurement"],"summary":summary,"cases":cases,"rho_cases":rho_cases}))?;
    println!("{}",serde_json::to_string(&summary)?);
    Ok(())
}

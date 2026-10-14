# Actual macOS observations — 0.13.0

Agent native-UI checks on October 13, 2026. These are not collaborator acceptance,
all-platform qualification or another endurance run. Final executable SHA-256:
`689ed9e13e6cdbea8774c232b88018eaebd0c8fcbd2aaedc2d0fb0c6e1bb3b5b`.
All model calls used the separately owned endpoint described in the frozen v3 plan;
no Being service was contacted.

## Legacy reading, pointer and reopen

The exact final package restored the existing qualification session
`sustained-1791919382664-3` with 121 steps and four journals. It remained paused and
Resume was disabled at its exhausted limits. Its omitted historical prompt version
was interpreted as v1 and displayed as `reservoir-journal-v1` inside Evidence.
The old immutable export was not changed. See [the receipt](native-pointer-legacy-01.json).

An older step-30 journal stayed selected through Cmd-M and native Finder reopen.
Finder initially held an unresolvable URL for the replaced pre-build app inode;
returning to its parent and reopening the package folder provided the actual app.
One offscreen Follow latest automation click only scrolled. After bringing the
button into view, a screenshot-grounded pointer click selected step 120 and enabled
Follow latest. A second cycle, with controls already visible, again preserved the
selection while minimized and responded to the visible Follow latest pointer click
after native reopen. Evidence responded too. The native export folder chooser opened,
and Cancel returned to the reader with the explicit cancellation status.

These results establish successful visible-target pointer actions in these checks.
They do not isolate the cause of the earlier intermittent pointer problem; some
failures involve automation focus/visibility or native dialog routing. The source
Reopen handler restores/shows/focuses the existing window without resuming a session.
The historical session was then explicitly stopped to permit a separate new session;
no Start or model request was issued for that historical session.

## New v3 run

The accepted setup was inspected before Start and captured in
[real-model-bound-before-start.json](real-model-bound-before-start.json). The new
session `sustained-1791923112800-6` uses generation `6`, prompt v3 and the frozen
121-step/four-attempt/600-second/64-MiB bounds. Actual Start advanced the numerical
clock. At step 30 the first response reported a token limit; the UI displayed:

- Writing attempt blocked.
- Incomplete or token-limited response cannot become journal feedback.
- No network request is active; no accepted journal or feedback and no automatic retry.

Request details identified turn/attempt 1/1 and the selected local source. The UI
showed zero saved journals and one retained attempt. Neither Retry nor Skip was
pressed. Three opportunities remained unstarted. No v3 saved prose, later memory
turn or new-run minimized continuation is claimed. See
[the held-state receipt](real-model-observation-02.json).

## Export and remaining blocker

Export committed session bundle opened the native directory chooser. The Go to
Folder sheet did not respond correctly to automation's Return/Escape inputs or
suggestion actions. Setting the exact directory through accessibility changed its
text, but submission returned to `/` rather than navigating. Rebinding the exact
app did not resolve this. User assistance to submit/dismiss the sheet was requested;
there is no completed native export or new-session relaunch/recovery claim yet.
Do not force-quit the app or retry the model to work around this UI check.

To continue independent inspection, an explicitly labeled passive copy retained the
four exact committed files under `target/qa/0.13-open-writing/held-evidence-copy-01`.
The manifest was stable throughout copying. This is a protocol deviation from
native-export collection, **not** a native export pass. Its pinned production replay
and subsequent reading checks are reported in [REAL-MODEL-RESULTS.md](REAL-MODEL-RESULTS.md).
Compare a later native export byte-for-byte before extending that claim.

The separately owned model service received TERM and is absent together with its
original process group. Its supervisor still reported a failed post-TERM stability
check; preserve that distinction in [the supplement](owned-model-cleanup-supplement-01.json).
The open application is held, with no active model request. The agent-created Finder
package window remains available for the pending native recovery check; unrelated
Finder windows were not changed.

## Completed follow-up after user assistance — October 13

The earlier blocker section remains the original observation. The user subsequently
reported dismissing/submitting the sheet. The next observation showed the parent
chooser at Macintosh HD. Reopening Go to Folder still did not accept pasted text;
explicitly invoking its exposed **Raise** action, setting the exact path and pressing
Return then navigated to the intended `target/qa/0.13-open-writing/exports` directory.
Open published `sustained-1791923112800-6-6-36`. Its four committed files exactly match
the passive copy, and the pinned verifier passes; see [the separate native supplement](NATIVE-EXPORT-SUPPLEMENT.md).
This qualifies the actual export operation after assistance, without assigning a
proven cause to every earlier pointer/input failure.

Cmd-Q exited cleanly; the exact executable process query was empty and the retained
manifest remained `ac1b87e3e8bc50689d28f36a73a8a2e5ee1de2091d30117dbbbb44c294d46ef4`.
The same package relaunched to the idle guide. My reservoir had no running session.
Read recovery catalog, Verify and inspect, then Restore paused for review restored
the exact session as generation 7/revision 37. The view showed Paused at step 30,
zero saved journals, one retained attempt, the incomplete-response reason and
**Resume explicitly disabled**. Accepted configuration retained
`reservoir-journal-v3`, the original endpoint/model and every original run bound.
No Start, Retry, Skip, service restart or readiness check was issued.

The restored snapshot was exported through the native chooser as
`sustained-1791923112800-6-7-37`. Its checkpoint remains
`a9a85f0f32db910bf3f86573d5103069acfbe533b0c9a1cfd2f86241099461ff`.
See [clean quit](native-clean-quit-01.json) and [recovery](native-recovery-completed-01.json).
The application is left paused for review. The agent-created Finder `macos` window
was closed; the user's pre-existing `journal` window was not operated on.
The model service remains stopped. This completes native export and clean recovery
for this held response, not a new successful journal or physical crash/sleep test.

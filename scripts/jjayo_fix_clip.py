#!/usr/bin/env python3
"""Patch a single verified WIPI graphics API bug in the pinned MIT emulator.
The old code dereferenced pv=0 in MC_grpSetContext(ClipIdx); KTF games use
a null clip pointer to restore the default (unclipped) context.
No game file is copied to CI or the public repository.
"""
from pathlib import Path
import glob
roots = [Path(x) for x in glob.glob(str(Path.home()/".cargo/git/checkouts/wie-*/**/wie-wipi-c/src/api/graphics.rs"),recursive=True)]
assert len(roots)==1, f"Expected one pinned WIPI graphics.rs, found {roots}"
p=roots[0]
s=p.read_text()
old='''        WIPICGraphicsContextIdx::ClipIdx => {
            let clip: [i32; 4] = read_generic(context, pv)?;
            grp_ctx.clip = clip.map(|value| value as u16);
        }'''
new='''        WIPICGraphicsContextIdx::ClipIdx => {
            if pv == 0 {
                // KTF may use a null clip pointer to disable a previous
                // clipping region. This is not a readable memory address.
                // Restore the normal default context clip instead of
                // performing read_generic(context, 0) and crashing.
                grp_ctx.clip = WIPICGraphicsContext::default().clip;
                tracing::debug!("MC_grpSetContext: reset clipping (null rectangle)");
            } else {
                let clip: [i32; 4] = read_generic(context, pv)?;
                grp_ctx.clip = clip.map(|value| value as u16);
            }
        }'''
assert s.count(old)==1, f"Expected old clip handler once, got {s.count(old)}"
p.write_text(s.replace(old,new,1))
print("Patched one WIPI ClipIdx NULL pointer dereference:",p)

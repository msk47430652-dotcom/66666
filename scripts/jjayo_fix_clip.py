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
assert s.count(old)==1, "Expected one clip reset"
s=s.replace(old,new,1)
old_repaint='''    let platform = context.system().platform();
    let screen = platform.screen();
    screen.request_redraw().unwrap();

    Ok(())
}'''
new_repaint='''    // Some KTF games (including JJayo Tycoon 3) only call MC_grpRepaint
    // after drawing to their screen framebuffer, never MC_grpFlushLcd.
    // A redraw request alone cannot display pixels in mobile CaptureScreen.
    // Capture the guest's real frontbuffer before requesting next redraw.
    let frontbuffer_ptr: u32 = read_generic(context, SCREEN_FRAMEBUFFER_PTR)?;
    if frontbuffer_ptr != 0 {
        let address = context.data_ptr(WIPICIndirectPtr(frontbuffer_ptr))?;
        let buffer = FrameBuffer(read_generic(context, address)?);
        let image = buffer.image(context)?;
        context.system().platform().screen().paint(&*image);
    }
    context.system().platform().screen().request_redraw()?;

    Ok(())
}'''
assert s.count(old_repaint)==1, f"Expected one repaint handler, found {s.count(old_repaint)}"
s=s.replace(old_repaint,new_repaint,1)
p.write_text(s)
print("Patched WIPI null clip and repaint frontbuffer capture:",p)

#!/usr/bin/env python3
"""Respect WIPI graphics context clipping when drawing.
Run after jjayo_fix_clip.py against the pinned upstream core checkout.
"""
from pathlib import Path
import glob

files=[Path(p) for p in glob.glob(str(Path.home()/".cargo/git/checkouts/wie-*/**/wie-wipi-c/src/api/graphics.rs"),recursive=True)]
assert len(files)==1,files
p=files[0]
s=p.read_text()
def change(old,new):
    global s
    n=s.count(old)
    assert n==1,(n,old[:100])
    s=s.replace(old,new,1)

# Need signed coordinate conversion: set_context deliberately stores the original
# signed i32 coordinates as u16 ABI words.
anchor='''pub async fn get_screen_framebuffer(context: &mut dyn WIPICContext, a0: WIPICWord) -> Result<WIPICIndirectPtr> {'''
helper='''// KTF MC_grpSetContext ClipIdx takes [left,top,right,bottom] as signed
// 32-bit coordinates. Its graphics context stores signed 16-bit words.
fn jjayo_clip(gctx: &WIPICGraphicsContext, fb: &FrameBuffer) -> Clip {
    let whole=Clip { x:0,y:0,width:fb.0.width,height:fb.0.height };
    let a=gctx.clip;
    if a==[0;4] {
        return whole; // A null ClipIdx resets the clip.
    }
    let left=(a[0] as i16) as i32;
    let top=(a[1] as i16) as i32;
    let right=(a[2] as i16) as i32;
    let bottom=(a[3] as i16) as i32;
    let clipped=Clip {
        x:left,
        y:top,
        width:(right as i64-left as i64).max(0) as u32,
        height:(bottom as i64-top as i64).max(0) as u32,
    };
    whole.intersect(&clipped)
}

'''
change(anchor,helper+anchor)

# Log only the first handful of active clip regions, not every frame.
change('''                grp_ctx.clip = clip.map(|value| value as u16);
            }
        }''',
'''                grp_ctx.clip = clip.map(|value| value as u16);
                static COUNT: core::sync::atomic::AtomicUsize=core::sync::atomic::AtomicUsize::new(0);
                if COUNT.fetch_add(1,core::sync::atomic::Ordering::Relaxed)<12 {
                    tracing::warn!("JJAYO_CONTEXT_CLIP {:?}", clip);
                }
            }
        }''')

change('''    let src_image = FrameBuffer(image.img).image(context)?;
    let clip = Clip {
        x: dx as _,
        y: dy as _,
        width: w as _,
        height: h as _,
    };

    primitives::draw_image(context, &framebuffer, dx, dy, w as u32, h as u32, &*src_image, sx, sy, clip)''',
'''    if w<=0 || h<=0 { return Ok(()); }
    let gctx: WIPICGraphicsContext = read_generic(context, graphics_context)?;
    let src_image = FrameBuffer(image.img).image(context)?;
    let image_area=Clip { x:dx, y:dy,width:w as u32,height:h as u32 };
    let clip=image_area.intersect(&jjayo_clip(&gctx,&framebuffer));
    primitives::draw_image(context, &framebuffer, dx, dy, w as u32, h as u32, &*src_image, sx, sy, clip)''')

# DrawString gets an entire framebuffer clip even after the game defined a region.
change('''    let clip = Clip {
        x: 0,
        y: 0,
        width: framebuffer.0.width,
        height: framebuffer.0.height,
    };

    let color = framebuffer.pixel_to_color(gctx.fgpxl);''',
'''    let clip = jjayo_clip(&gctx, &framebuffer);

    let color = framebuffer.pixel_to_color(gctx.fgpxl);''')

p.write_text(s)
print("Patched KTF graphics-context clipping for DrawImage and DrawString",p)

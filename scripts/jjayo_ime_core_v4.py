#!/usr/bin/env python3
"""KTF MC_im text input implementation for legacy feature-phone titles.
Mapping verified against the MC_im* API order (Handle, SetMode, GetMode, Count, Modes).
User's original game data never enters this public repository.
"""
from pathlib import Path
import glob

root=Path(glob.glob(str(Path.home()/".cargo/git/checkouts/wie-*/**/wie-ktf/src/lib.rs"),recursive=True)[0]).parents[1]
src=root/"src/runtime/wipi_c/method_table.rs"
s=src.read_text()
a="use alloc::{format, vec, vec::Vec};"
assert s.count(a)==1
s=s.replace(a,"use alloc::{collections::VecDeque, format, string::ToString, vec, vec::Vec};\nuse core::sync::atomic::{AtomicI32, Ordering};\nuse spin::Mutex;",1)
a="use wie_util::{Result, WieError};"
assert s.count(a)==1
s=s.replace(a,"use wie_util::{read_generic, write_generic, Result, WieError};",1)
a="""        gen_unk_stub(3, 0),
        gen_unk_stub(3, 1),
        gen_unk_stub(3, 2),"""
b="""        jjayo_im_handle.into_body(),
        jjayo_im_set_mode.into_body(),
        jjayo_im_get_mode.into_body(),"""
assert s.count(a)==1
s=s.replace(a,b,1)
a="pub fn get_unk3_method_table() -> Vec<WIPICMethodBody> {"
new= r'''
/// Each queued UTF-16 Unicode codepoint becomes one complete EUC-KR character
/// on a subsequent MC_imHandleInput call. No guest code or saved data is altered.
static JJAYO_PENDING: Mutex<Option<VecDeque<Vec<u8>>>> = Mutex::new(None);
static JJAYO_MODE: AtomicI32 = AtomicI32::new(2);

pub fn jjayo_queue_guest_name(text: &str) -> usize {
    let mut queue = VecDeque::new();
    for ch in text.chars().take(4) {
        let (bytes, _encoding, had_errors) = encoding_rs::EUC_KR.encode(&ch.to_string());
        if !had_errors && !bytes.is_empty() && bytes.len() <= 4 {
            queue.push_back(bytes.to_vec());
        }
    }
    let len = queue.len();
    *JJAYO_PENDING.lock() = if len > 0 { Some(queue) } else { None };
    len
}

async fn jjayo_im_set_mode(_ctx: &mut dyn WIPICContext, mode: i32) -> Result<i32> {
    let supported=(0..4).contains(&mode);
    if supported { JJAYO_MODE.store(mode, Ordering::Relaxed); }
    tracing::debug!("KTF MC_imSetCurrentMode({mode}) => {supported}");
    Ok(if supported { 1 } else { 0 })
}
async fn jjayo_im_get_mode(_ctx: &mut dyn WIPICContext) -> Result<i32> {
    Ok(JJAYO_MODE.load(Ordering::Relaxed))
}

/// M_Int32 MC_imHandleInput(char key, M_Int32 type,
///    char *complete, M_Int32 *complete_size, char *composing, M_Int32 *composing_size).
/// Both *_size pointers contain buffer capacities on entry and data lengths on return.
async fn jjayo_im_handle(
    ctx: &mut dyn WIPICContext,
    key: u32, event_type: i32,
    complete: u32, complete_size: u32,
    composing: u32, composing_size: u32,
) -> Result<i32> {
    if complete_size == 0 || composing_size == 0 { return Ok(0); }
    let capacity: i32 = read_generic(ctx, complete_size)?;
    let _: i32 = read_generic(ctx, composing_size)?;
    write_generic(ctx, complete_size, 0i32)?;
    write_generic(ctx, composing_size, 0i32)?;

    // WIPI KEY_PRESSED=1. Never duplicate a character on key release.
    if event_type != 2 { return Ok(0); }
    let queued = JJAYO_PENDING.lock().as_ref().and_then(|q| q.front().cloned());
    let payload = if let Some(bytes) = queued {
        Some((bytes, true))
    } else {
        // Standard numeric keypad fallback. Android keyboard supports proper Hangul.
        // Digits stay digits rather than inserting invalid/guessed Hangul syllables.
        match key {
            0x30..=0x39 => Some((vec![key as u8],false)),
            0x20 => Some((vec![b' '],false)),
            _ => None,
        }
    };
    if let Some((bytes, from_keyboard)) = payload {
        // Do not overwrite caller's data or null pointer.
        if complete != 0 && capacity >= bytes.len() as i32 && capacity <= 4096 {
            ctx.write_bytes(complete, &bytes)?;
            write_generic(ctx, complete_size, bytes.len() as i32)?;
            if from_keyboard {
                let mut queue=JJAYO_PENDING.lock();
                if let Some(pending)=queue.as_mut() {
                    pending.pop_front();
                    if pending.is_empty() { *queue = None; }
                }
            }
            tracing::debug!("KTF MC_imHandleInput key={key:#x} committed={} bytes",bytes.len());
        } else {
            tracing::warn!("KTF MC_imHandleInput buffer insufficient: key={key:#x} cap={capacity}");
        }
        return Ok(0);
    }
    // Preserve the phone key code for control keys (OK/Clear/soft keys).
    Ok(key as i32)
}

'''
assert s.count(a)==1
s=s.replace(a,new+a,1)
src.write_text(s)
print("Patched KTF input mode and UTF-8 → EUC-KR character buffer:",src)

# Surface the guest text queue to the Android JNI bridge, without changing the engine ABI.
p=root/"src/runtime/wipi_c.rs"
s=p.read_text()
s+='''

pub(crate) fn jjayo_queue_guest_name(text: &str) -> usize {
    method_table::jjayo_queue_guest_name(text)
}
'''
p.write_text(s)
p=root/"src/runtime.rs"
s=p.read_text()
s+='''

pub(crate) fn jjayo_queue_guest_name(text: &str) -> usize {
    wipi_c::jjayo_queue_guest_name(text)
}
'''
p.write_text(s)
p=root/"src/lib.rs"
s=p.read_text()
s+='''

pub fn queue_guest_name(text: &str) -> usize {
    runtime::jjayo_queue_guest_name(text)
}
'''
p.write_text(s)
print("Exported wie_ktf::queue_guest_name")

# Android and Linux shared host session; text can be entered from Android JNI.
p=Path(__import__("sys").argv[1])/"rust/wipi_core/src/session.rs"
s=p.read_text()
anchor="pub fn key_down(key: &str) {"
assert s.count(anchor)==1
s=s.replace(anchor,'''/// Stage up to 4 complete characters for the Clet input-method callback.
pub fn queue_guest_name(text: &str) -> i32 {
    wie_ktf::queue_guest_name(text) as i32
}

'''+anchor,1)
p.write_text(s)
p=Path(__import__("sys").argv[1])/"rust/wipi_android/src/jni_bridge.rs"
s=p.read_text()
anchor='''#[unsafe(no_mangle)]
pub extern "system" fn Java_com_parkjeongseop_wipi_WipiNative_nativeKeyDown'''
assert s.count(anchor)==1
s=s.replace(anchor,'''#[unsafe(no_mangle)]
pub extern "system" fn Java_com_parkjeongseop_wipi_WipiNative_nativeQueueText(
    mut env: JNIEnv, _class: JClass, input: JString
) -> i32 {
    match env.get_string(&input) {
        Ok(name) => session::queue_guest_name(&String::from(name)),
        Err(_) => 0,
    }
}

'''+anchor,1)
p.write_text(s)
print("Added WIPI Android JNI nativeQueueText function.")


# Export the same function to the Linux headless tester, which can
# verify that a Korean name is genuinely accepted by the guest game.
p=Path(__import__("sys").argv[1])/"rust/wipi_android/src/lib.rs"
s=p.read_text()
s+='''

pub use wipi_core::session::queue_guest_name;
'''
p.write_text(s)
p=Path(__import__("sys").argv[1])/"rust/wipi_android/src/bin/headless.rs"
s=p.read_text()
anchor="    let start = std::time::Instant::now();"
assert s.count(anchor)==1
s=s.replace(anchor,'''    if let Ok(name) = std::env::var("JJAYO_TEST_NAME") {
        eprintln!("JJAYO_TEST_QUEUED={}", wipi_android::queue_guest_name(&name));
    }

'''+anchor,1)
p.write_text(s)
print("Linux headless runner supports JJAYO_TEST_NAME for Korean text verification.")

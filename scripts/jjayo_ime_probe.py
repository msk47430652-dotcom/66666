#!/usr/bin/env python3
"""Trace KTF interface3 unresolved text-input calls without changing semantics.
Contains no proprietary game assets; use only with pinned wie emulator checkout.
"""
from pathlib import Path
import glob
items=list(Path.home().glob(".cargo/git/checkouts/wie-*/**/wie-ktf/src/runtime/wipi_c/method_table.rs"))
assert len(items)==1,items
path=items[0]
s=path.read_text(encoding="utf-8")
old="""        gen_unk_stub(3, 0),
        gen_unk_stub(3, 1),
        gen_unk_stub(3, 2),"""
new="""        jjayo_probe_im0.into_body(),
        gen_unk_stub(3, 1),
        gen_unk_stub(3, 2),"""
assert s.count(old)==1
s=s.replace(old,new,1)
needle="pub fn get_unk3_method_table() -> Vec<WIPICMethodBody> {"
probe="""async fn jjayo_probe_im0(
    _ctx: &mut dyn WIPICContext,
    a0:u32, a1:u32, a2:u32, a3:u32, a4:u32,
    a5:u32, a6:u32, a7:u32, a8:u32,
) -> wie_util::Result<u32> {
    tracing::warn!("JJAYO_IM0_ARGS {a0:#x} {a1:#x} {a2:#x} {a3:#x} {a4:#x} {a5:#x} {a6:#x} {a7:#x} {a8:#x}");
    Ok(0)
}
"""
assert s.count(needle)==1
s=s.replace(needle,probe+"\n"+needle,1)
path.write_text(s,encoding="utf-8")
print("KTF interface3 method0 arguments instrumented:",path)

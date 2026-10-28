#!/usr/bin/env python3
"""Instrument only an open-source Linux test build. No game file is uploaded."""
from pathlib import Path
import glob
roots = [Path(x) for x in glob.glob(str(Path.home() / ".cargo/git/checkouts/wie-*/**/wie-util/src/lib.rs"), recursive=True)]
assert len(roots)==1, f"expected pinned wie-util source: {roots}"
path=roots[0]
source=path.read_text()
assert "#![no_std]\n" in source
source=source.replace("#![no_std]\n", "#![no_std]\n#[cfg(target_os = \"linux\")]\nextern crate std;\n",1)
intro='''#[cfg(target_os = "linux")]
fn jjayo_debug_null_access(operation: &str) {
    static SEEN: core::sync::atomic::AtomicUsize = core::sync::atomic::AtomicUsize::new(0);
    let prev = SEEN.fetch_add(1, core::sync::atomic::Ordering::Relaxed);
    if prev < 6 {
        std::eprintln!("JJAYO_NULL_ACCESS #{} in {}\\n{:?}", prev, operation,
            std::backtrace::Backtrace::force_capture());
    }
}

'''
anchor='pub trait ByteRead {'
assert source.count(anchor)==1
source=source.replace(anchor,intro+anchor,1)
funcs=["pub fn read_generic<", "pub fn read_null_terminated_string_bytes<",
       "pub fn write_generic<", "pub fn read_null_terminated_table<"]
for func in funcs:
    start=source.index(func)
    if_addr=source.index("    if address == 0 {",start) if func not in ("pub fn read_null_terminated_table<",) else source.index("    if base_address == 0 {",start)
    where=source.index("\n",if_addr)+1
    source=source[:where]+'''        #[cfg(target_os = "linux")]
        jjayo_debug_null_access("'''+func.split('<')[0]+'''");\n'''+source[where:]
path.write_text(source)
print("Debug instrumentation applied:",path)

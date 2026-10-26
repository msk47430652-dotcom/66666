from pathlib import Path
import sys
import re

r = Path(sys.argv[1])
main = r / "android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
session = r / "rust/wipi_core/src/session.rs"
gradle = r / "android/app/build.gradle.kts"

s = session.read_text()
a = "    while !stop.load(Ordering::SeqCst) {\n        // 일시정지:"
assert s.count(a) == 1
s = s.replace(a, "    while !stop.load(Ordering::SeqCst) {\n        let cycle_start = Instant::now();\n        // 일시정지:", 1)
a = "        }\n    }\n}\n\n/// 게임을 로드하고 에뮬레이터 스레드를 시작한다."
assert s.count(a) == 1
s = s.replace(a, """        }
        let budget = std::time::Duration::from_millis(33);
        if let Some(rest) = budget.checked_sub(cycle_start.elapsed()) {
            std::thread::sleep(rest);
        }
    }
}

/// 게임을 로드하고 에뮬레이터 스레드를 시작한다.""", 1)
session.write_text(s)

files = list(Path.home().glob(".cargo/git/checkouts/wie-*/**/wie-wipi-c/src/api/kernel/sprintf.rs"))
assert len(files) == 1, files
p = files[0]
s = p.read_text()
a = "                '.' => precision = Some(0),"
assert s.count(a) == 1
s = s.replace(a, """                '.' => precision = Some(0),
                '*' if precision.is_some() => {
                    let amount = next_arg(&mut arg_iter) as i32;
                    precision = Some(if amount < 0 { MAX_WIDTH } else { (amount as usize).min(MAX_WIDTH) });
                },""", 1)
a = "    #[test]\n    fn test_unknown_specifier_passthrough() -> Result<()> {"
assert s.count(a) == 1
s = s.replace(a, """    #[test]
    fn test_wildfrontier_dialogue_dynamic_precision() -> Result<()> {
        assert_eq!(format("[%.*s]", &[2, 0x50])?, "[st]");
        assert_eq!(format("%.*s!", &[4, 0x50])?, "stub!");
        Ok(())
    }

"""+a,1)
p.write_text(s)

s = main.read_text()
a = "        var showSettings by remember { mutableStateOf(false) } // iOS sheet 대응 오버레이\n"
assert s.count(a) == 1
s = s.replace(a,a+"""
        LaunchedEffect(Unit) {
            try {
                val saveDir = File(filesDir, "wildfrontier_save")
                saveDir.mkdirs()
                val bundledGame = assets.open("wildfrontier.zip").use { it.readBytes() }
                if (start(bundledGame, "wildfrontier.zip", saveDir)) {
                    errorMessage = null
                    screen = Screen.Emulator
                } else {
                    errorMessage = pendingError() ?: getString(R.string.error_start_failed)
                }
            } catch (e: Exception) {
                errorMessage = "Wild Frontier: " + (e.message ?: "Missing game")
            }
        }
""",1)
main.write_text(s)

s = gradle.read_text()
assert 'applicationId = "com.parkjeongseop.wipi"' in s
s = s.replace('applicationId = "com.parkjeongseop.wipi"', 'applicationId = "org.wildfrontier.personal"')
s = s.replace('abiFilters += listOf("arm64-v8a", "x86_64")', 'abiFilters += listOf("arm64-v8a")')
gradle.write_text(s)
for f in (r / "android/app/src/main/res").glob("values*/strings.xml"):
    s = f.read_text()
    s = re.sub(r'<string name="app_name">[^<]+</string>', '<string name="app_name">와일드프론티어</string>', s)
    f.write_text(s)
print("PATCH OK: text, speed, startup")

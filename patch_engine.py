from pathlib import Path
import re, sys

r=Path(sys.argv[1])
main=r/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
native=r/"android/app/src/main/java/com/parkjeongseop/wipi/WipiNative.kt"
session=r/"rust/wipi_core/src/session.rs"
screen=r/"rust/wipi_core/src/platform/screen.rs"
bridge=r/"rust/wipi_android/src/jni_bridge.rs"
gradle=r/"android/app/build.gradle.kts"

# The former patches slept AFTER EVERY emulator.tick(), which is not one game frame.
# Only pace completed screen paints. Run arbitrary numbers of internal ticks
# between paints to preserve guest timers, input processing, and script progress.
s=screen.read_text()
assert s.count('    dirty: AtomicBool,')==1
s=s.replace('    dirty: AtomicBool,','    dirty: AtomicBool,\n    frame_serial: std::sync::atomic::AtomicU64,')
assert s.count('            dirty: AtomicBool::new(false),')==1
s=s.replace('            dirty: AtomicBool::new(false),','            dirty: AtomicBool::new(false),\n            frame_serial: std::sync::atomic::AtomicU64::new(0),')
assert s.count('    pub fn take_redraw_request(&self) -> bool {')==1
s=s.replace('    pub fn take_redraw_request(&self) -> bool {', '''    pub fn frame_serial(&self) -> u64 {
        self.frame_serial.load(Ordering::Relaxed)
    }

    pub fn take_redraw_request(&self) -> bool {''')
assert s.count('        self.dirty.store(true, Ordering::SeqCst);')==1
s=s.replace('        self.dirty.store(true, Ordering::SeqCst);','        self.dirty.store(true, Ordering::SeqCst);\n        self.frame_serial.fetch_add(1, Ordering::Relaxed);')
screen.write_text(s)

s=session.read_text()
assert s.count('static SESSION: Mutex<Option<Session>> = Mutex::new(None);')==1
s=s.replace('static SESSION: Mutex<Option<Session>> = Mutex::new(None);',
'''static SESSION: Mutex<Option<Session>> = Mutex::new(None);
// 0 = unrestricted screen paints. The value is updated by the in-game UI.
static FRAME_INTERVAL_MS: std::sync::atomic::AtomicU64 =
    std::sync::atomic::AtomicU64::new(33);

/// Limit screen presentation rate, NOT the number of core emulation ticks.
pub fn set_frame_limit(fps: i32) {
    let interval = match fps {
        15 => 67,
        20 => 50,
        30 => 33,
        45 => 22,
        60 => 16,
        0 => 0,
        _ => 33,
    };
    FRAME_INTERVAL_MS.store(interval, Ordering::Relaxed);
}''')
assert s.count('    let mut pressed: HashMap<KeyCode, Instant> = HashMap::new();')==1
s=s.replace('    let mut pressed: HashMap<KeyCode, Instant> = HashMap::new();',
'''    let mut pressed: HashMap<KeyCode, Instant> = HashMap::new();
    let mut last_frame_serial = platform.screen_capture().frame_serial();
    let mut last_paint_time = Instant::now();''')
anchor='''        }
    }
}

/// 게임을 로드하고 에뮬레이터 스레드를 시작한다.'''
assert s.count(anchor)==1
s=s.replace(anchor,'''        }

        // Screen paints are meaningful game frames; executor ticks are not.
        // Never sleep after an internal tick that did not paint anything.
        let frame_serial = platform.screen_capture().frame_serial();
        if frame_serial != last_frame_serial {
            last_frame_serial = frame_serial;
            let limit_ms = FRAME_INTERVAL_MS.load(Ordering::Relaxed);
            if limit_ms > 0 {
                let budget = std::time::Duration::from_millis(limit_ms);
                if let Some(rest) = budget.checked_sub(last_paint_time.elapsed()) {
                    std::thread::sleep(rest);
                }
            }
            last_paint_time = Instant::now();
        }
    }
}

/// 게임을 로드하고 에뮬레이터 스레드를 시작한다.''',1)
assert 'cycle_start' not in s
session.write_text(s)

s=bridge.read_text()
a='''/// 볼륨 (0.0~1.0, 0이면 음소거)'''
assert s.count(a)==1
s=s.replace(a,'''#[unsafe(no_mangle)]
pub extern "system" fn Java_com_parkjeongseop_wipi_WipiNative_nativeSetFrameLimit(
    _env: JNIEnv, _class: JClass, fps: i32,
) {
    session::set_frame_limit(fps);
}

/// 볼륨 (0.0~1.0, 0이면 음소거)''',1)
bridge.write_text(s)

s=native.read_text()
a='''    external fun nativeSetPaused(paused: Boolean)'''
assert s.count(a)==1
s=s.replace(a,a+'''\n\n    /** Limits screen paints only; core emulation ticks are never capped. 0 disables the limit. */
    external fun nativeSetFrameLimit(fps: Int)''',1)
native.write_text(s)

s=main.read_text()
a='''        var showSettings by remember { mutableStateOf(false) } // iOS sheet 대응 오버레이
'''
assert s.count(a)==1
s=s.replace(a,a+'''
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
''',1)
a='''        var paused by remember { mutableStateOf(false) }'''
assert s.count(a)==1
s=s.replace(a,a+'''\n        var fpsLimit by remember { mutableStateOf(30) }''',1)
a='''            // 우상단: 일시정지 + 설정 (iOS와 동일 구성)'''
assert s.count(a)==1
s=s.replace(a,'''            // Explicit in-game frame rate control for old WIPI titles.
            // A player can select the smoothest real-time rate without rebuilding the APK.
            Row(modifier = Modifier.align(Alignment.TopStart)) {
                IconButton(onClick = {
                    fpsLimit = when (fpsLimit) {
                        30 -> 45
                        45 -> 60
                        60 -> 0
                        0 -> 20
                        20 -> 15
                        else -> 30
                    }
                    WipiNative.nativeSetFrameLimit(fpsLimit)
                }) {
                    Text(if (fpsLimit == 0) "MAX" else "${fpsLimit}FPS",
                        color = Color.White, fontSize = 12.sp)
                }
            }

            // 우상단: 일시정지 + 설정 (iOS와 동일 구성)''',1)
main.write_text(s)

files=list(Path.home().glob(".cargo/git/checkouts/wie-*/**/wie-wipi-c/src/api/kernel/sprintf.rs"))
assert len(files)==1,files
p=files[0]
s=p.read_text()
a="                '.' => precision = Some(0),"
assert s.count(a)==1
s=s.replace(a,'''                '.' => precision = Some(0),
                '*' if precision.is_some() => {
                    let amount = next_arg(&mut arg_iter) as i32;
                    precision = Some(if amount < 0 { MAX_WIDTH } else { (amount as usize).min(MAX_WIDTH) });
                },''',1)
a='''    #[test]
    fn test_unknown_specifier_passthrough() -> Result<()> {'''
assert s.count(a)==1
s=s.replace(a,'''    #[test]
    fn test_wildfrontier_dialogue_dynamic_precision() -> Result<()> {
        assert_eq!(format("[%.*s]", &[2, 0x50])?, "[st]");
        assert_eq!(format("%.*s!", &[4, 0x50])?, "stub!");
        Ok(())
    }

'''+a,1)
p.write_text(s)

s=gradle.read_text()
assert 'applicationId = "com.parkjeongseop.wipi"' in s
s=s.replace('applicationId = "com.parkjeongseop.wipi"','applicationId = "org.wildfrontier.personal"')
s=s.replace('abiFilters += listOf("arm64-v8a", "x86_64")','abiFilters += listOf("arm64-v8a")')
gradle.write_text(s)
for f in (r/"android/app/src/main/res").glob("values*/strings.xml"):
    s=f.read_text()
    s=re.sub(r'<string name="app_name">[^<]+</string>', '<string name="app_name">와일드프론티어</string>', s)
    f.write_text(s)
print("FRAME-PACED WIPI: ticks unrestricted; 15/20/30/45/60/MAX screen limit.")

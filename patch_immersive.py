from pathlib import Path
import sys
p=Path(sys.argv[1])/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
s=p.read_text()
s="@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)\n\n"+s
needle="import androidx.compose.foundation.layout.fillMaxWidth\n"
assert s.count(needle)==1
s=s.replace(needle,needle+"""import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.navigationBarsIgnoringVisibility
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
""",1)
needle="    override fun onCreate(savedInstanceState: Bundle?) {\n        super.onCreate(savedInstanceState)\n"
assert s.count(needle)==1
s=s.replace(needle,"""    private fun hideSystemBars() {
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val controller = WindowCompat.getInsetsController(window, window.decorView)
        controller.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        controller.hide(WindowInsetsCompat.Type.systemBars())
    }
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideSystemBars()
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        hideSystemBars()
""",1)
a=s.rfind('\n', 0, s.index('Row(modifier = Modifier.align(Alignment.TopStart)) {')) + 1
b=s.index('            // 우상단: 일시정지 + 설정 (iOS와 동일 구성)',a)
s=s[:a]+s[b:]
a=s.index('            // 우상단: 일시정지 + 설정 (iOS와 동일 구성)')
b=s.index('            if (paused) {',a)
s=s[:a]+s[b:]
needle='Column(modifier = Modifier.fillMaxSize().background(Color(0xFF202020))) {'
assert s.count(needle)==1
s=s.replace(needle,'''Column(
                modifier = Modifier.fillMaxSize()
                    .background(Color(0xFF202020))
                    .safeDrawingPadding()
            ) {''',1)
needle='Keypad(hapticsEnabled = settings.keypadHaptics, modifier = Modifier.fillMaxWidth().padding(8.dp))'
assert s.count(needle)==1
s=s.replace(needle,'''Keypad(
                    hapticsEnabled = settings.keypadHaptics,
                    modifier = Modifier.fillMaxWidth()
                        .windowInsetsPadding(WindowInsets.navigationBarsIgnoringVisibility.only(WindowInsetsSides.Bottom))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    fpsLimit = fpsLimit,
                    onFpsChange = {
                        fpsLimit = when (fpsLimit) {
                            30 -> 45
                            45 -> 60
                            60 -> 0
                            0 -> 20
                            20 -> 15
                            else -> 30
                        }
                        WipiNative.nativeSetFrameLimit(fpsLimit)
                    },
                    onPause = {
                        if (!paused) {
                            paused = true
                            WipiNative.nativeSetPaused(true)
                        }
                    },
                    onSettings = onSettings,
                )''',1)
needle='fun Keypad(hapticsEnabled: Boolean, modifier: Modifier = Modifier) {'
assert s.count(needle)==1
s=s.replace(needle,'''fun Keypad(
    hapticsEnabled: Boolean,
    modifier: Modifier = Modifier,
    fpsLimit: Int = 30,
    onFpsChange: () -> Unit = {},
    onPause: () -> Unit = {},
    onSettings: () -> Unit = {},
) {''',1)
needle='''        TextButton(
            onClick = { showNumeric = !showNumeric },
            modifier = Modifier.height(42.dp),
        ) {
            Text(if (showNumeric) "숫자키 접기 ▲" else "숫자키 펼치기 ▼", fontSize = 12.sp)
        }'''
assert s.count(needle)==1
s=s.replace(needle,'''        Row(
            modifier = Modifier.fillMaxWidth().height(48.dp),
            horizontalArrangement = Arrangement.spacedBy(3.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            TextButton(
                onClick = { showNumeric = !showNumeric },
                modifier = Modifier.weight(1.3f).height(48.dp),
            ) {
                Text(if (showNumeric) "숫자 접기" else "숫자키", fontSize = 12.sp)
            }
            TextButton(onClick = onFpsChange, modifier = Modifier.weight(1.2f).height(48.dp)) {
                Text(if (fpsLimit == 0) "MAX" else fpsLimit.toString() + "FPS", fontSize = 12.sp)
            }
            IconButton(onClick = onPause, modifier = Modifier.size(48.dp)) {
                Icon(Icons.Filled.Pause, contentDescription = "일시정지", tint = Color.White)
            }
            IconButton(onClick = onSettings, modifier = Modifier.size(48.dp)) {
                Icon(Icons.Filled.Settings, contentDescription = "설정", tint = Color.White)
            }
        }''',1)
assert 'Modifier.align(Alignment.TopStart)' not in s
assert 'Modifier.align(Alignment.TopEnd)' not in s[s.index('private fun EmulatorScreen'):s.index('private fun LibraryScreen')]
p.write_text(s)
print("Immersive navigation, top bar and accessible FPS key patched")

from pathlib import Path
import sys
root = Path(sys.argv[1])
activity = root/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
gradle = root/"android/app/build.gradle.kts"
s=activity.read_text()
a=s.index("// ── 키패드 (iOS Keypad와 동일:")
assert a > 20000, a
s=s[:a]+"""
// ── Wild Frontier S26 compact touchscreen keypad ──
// The original 21-key 7-row keyboard shrank the actual game display.
// Default controls are movement, numeric 5, accept/back and two softkeys.
// An optional compact number pad remains available for rare gameplay prompts.

@Composable
fun Keypad(hapticsEnabled: Boolean, modifier: Modifier = Modifier) {
    var showNumeric by remember { mutableStateOf(false) }
    val keySpacing = 4.dp
    val dpadHeight = 54.dp
    val actionHeight = 83.dp

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // A left-hand D-pad with a real NUM5 center action. Blank corners
            // are non-pressable to prevent accidental input while moving.
            Column(
                modifier = Modifier.weight(1.6f),
                verticalArrangement = Arrangement.spacedBy(keySpacing),
            ) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(keySpacing)) {
                    Spacer(modifier = Modifier.weight(1f).height(dpadHeight))
                    KeyButton("UP", "▲", hapticsEnabled, Modifier.weight(1f), dpadHeight)
                    Spacer(modifier = Modifier.weight(1f).height(dpadHeight))
                }
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(keySpacing)) {
                    KeyButton("LEFT", "◀", hapticsEnabled, Modifier.weight(1f), dpadHeight)
                    KeyButton("5", "5", hapticsEnabled, Modifier.weight(1f), dpadHeight)
                    KeyButton("RIGHT", "▶", hapticsEnabled, Modifier.weight(1f), dpadHeight)
                }
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(keySpacing)) {
                    Spacer(modifier = Modifier.weight(1f).height(dpadHeight))
                    KeyButton("DOWN", "▼", hapticsEnabled, Modifier.weight(1f), dpadHeight)
                    Spacer(modifier = Modifier.weight(1f).height(dpadHeight))
                }
            }
            // Right-thumb actions, independently reachable without stretching.
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(keySpacing)) {
                    KeyButton("OK", "확인", hapticsEnabled, Modifier.weight(1f), actionHeight)
                    KeyButton("CLR", "취소", hapticsEnabled, Modifier.weight(1f), actionHeight)
                }
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(keySpacing)) {
                    KeyButton("SOFT_L", "L", hapticsEnabled, Modifier.weight(1f), actionHeight)
                    KeyButton("SOFT_R", "R", hapticsEnabled, Modifier.weight(1f), actionHeight)
                }
            }
        }
        // No dial/call key in the normal in-game keypad.
        // All numeric keys can be revealed for occasional game prompts.
        TextButton(
            onClick = { showNumeric = !showNumeric },
            modifier = Modifier.height(42.dp),
        ) {
            Text(if (showNumeric) "숫자키 접기 ▲" else "숫자키 펼치기 ▼", fontSize = 12.sp)
        }
        if (showNumeric) {
            listOf(
                listOf("1", "2", "3"),
                listOf("4", "5", "6"),
                listOf("7", "8", "9"),
                listOf("*", "0", "#"),
            ).forEach { row ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(keySpacing),
                ) {
                    row.forEach { key ->
                        KeyButton(key, key, hapticsEnabled, Modifier.weight(1f), 43.dp)
                    }
                }
            }
        }
    }
}

@Composable
fun KeyButton(
    key: String,
    label: String,
    hapticsEnabled: Boolean,
    modifier: Modifier = Modifier,
    buttonHeight: androidx.compose.ui.unit.Dp = 44.dp,
) {
    var pressed by remember(key) { mutableStateOf(false) }
    val view = androidx.compose.ui.platform.LocalView.current
    val baseColor = if (key == "OK") Color(0xFF345B62) else Color(0xFF383C41)

    Box(
        modifier = modifier
            .height(buttonHeight)
            .background(
                if (pressed) Color(0xFF5B7578) else baseColor,
                RoundedCornerShape(12.dp)
            )
            .pointerInput(key) {
                detectTapGestures(onPress = {
                    pressed = true
                    if (hapticsEnabled)
                        view.performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY)
                    WipiNative.nativeKeyDown(key)
                    try {
                        awaitRelease()
                    } finally {
                        pressed = false
                        WipiNative.nativeKeyUp(key)
                    }
                })
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = Color.White, fontSize = if (label.length > 2) 14.sp else 17.sp)
    }
}
"""
assert 'private val KEYPAD_ROWS' not in s
assert 'KeyButton("CALL"' not in s
assert 'fun Keypad(hapticsEnabled: Boolean' in s
activity.write_text(s)
g=gradle.read_text()
assert 'versionCode = 5 ' in g
g=g.replace('versionCode = 5 ', 'versionCode = 6 ')
gradle.write_text(g)
print("Keypad compacted to 5-way + OK/CLR + L/R with optional numerics, 6dp spacing, 54dp D-pad; versionCode 6")

#!/usr/bin/env python3
"""Samsung Korean keyboard entry for legacy WIPI Clet name boxes.
Run after patch_jjayo3_shell.py and jjayo_s26_ui_v3.py.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
java=root/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
s=java.read_text(encoding="utf-8")
def patch(old,new):
    global s
    n=s.count(old)
    assert n==1,("MainActivity mismatch",n,old[:140])
    s=s.replace(old,new,1)
patch("import androidx.compose.material3.Button\n",
      "import androidx.compose.material3.Button\nimport androidx.compose.material3.OutlinedTextField\n")
patch("import androidx.compose.runtime.remember\n",
      "import androidx.compose.runtime.remember\nimport androidx.compose.runtime.rememberCoroutineScope\n")
patch("import kotlinx.coroutines.isActive\n",
      "import kotlinx.coroutines.isActive\nimport kotlinx.coroutines.launch\nimport kotlinx.coroutines.delay\n")
patch('''        var paused by remember { mutableStateOf(false) }

        // 시스템 뒤로가기''',
'''        var paused by remember { mutableStateOf(false) }
        var showKoreanKeyboard by remember { mutableStateOf(false) }
        var typedName by remember { mutableStateOf("") }
        val inputScope = rememberCoroutineScope()

        // 시스템 뒤로가기''')
patch('''                Keypad(hapticsEnabled = settings.keypadHaptics, modifier = Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 4.dp))''',
'''                // The original WIPI handset input API is incomplete on Android.
                // Accept Korean text in an Android IME and commit it via KTF Clet IM API.
                TextButton(onClick = { typedName = ""; showKoreanKeyboard = true },
                    modifier = Modifier.fillMaxWidth().height(33.dp)) {
                    Text("⌨ 한글 이름 입력", color = Color.White, fontSize = 13.sp)
                }
                Keypad(hapticsEnabled = settings.keypadHaptics, modifier = Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 4.dp))''')
patch('''            if (paused) {
                Box(
                    modifier = Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.6f))''',
'''            if (showKoreanKeyboard) {
                AlertDialog(
                    onDismissRequest = { showKoreanKeyboard = false },
                    title = { Text("이름 입력") },
                    text = {
                        OutlinedTextField(
                            value = typedName,
                            onValueChange = { typedName = it.filter { c ->
                                c in '\\uAC00'..'\\uD7A3' || c in 'A'..'Z' || c in 'a'..'z' || c.isDigit()
                            }.take(4) },
                            label = { Text("한글 최대 4글자") },
                            singleLine = true,
                        )
                    },
                    confirmButton = {
                        TextButton(
                            enabled = typedName.isNotBlank(),
                            onClick = {
                                val count = WipiNative.nativeQueueText(typedName)
                                if (count > 0) {
                                    showKoreanKeyboard = false
                                    // The game consumes a single emulated input event
                                    // for each complete EUC-KR character.
                                    inputScope.launch {
                                        repeat(count) {
                                            WipiNative.nativeKeyDown("2")
                                            delay(72)
                                            WipiNative.nativeKeyUp("2")
                                            delay(120)
                                        }
                                    }
                                }
                            },
                        ) { Text("게임에 입력") }
                    },
                    dismissButton = {
                        TextButton(onClick = { showKoreanKeyboard = false }) { Text("취소") }
                    }
                )
            }

            if (paused) {
                Box(
                    modifier = Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.6f))''')
java.write_text(s,encoding="utf-8")

native=root/"android/app/src/main/java/com/parkjeongseop/wipi/WipiNative.kt"
s=native.read_text(encoding="utf-8")
old='    external fun nativeKeyDown(key: String)\n'
assert s.count(old)==1
s=s.replace(old,old+'''
    /** Queue up to four complete Korean/Latin characters for KTF MC_imHandleInput. */
    external fun nativeQueueText(text: String): Int
''',1)
native.write_text(s,encoding="utf-8")

gradle=root/"android/app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'versionCode = 6' in s
gradle.write_text(s.replace('versionCode = 6','versionCode = 7',1),encoding="utf-8")
print("Android native Korean name-entry dialog + JNI API + version7 added")

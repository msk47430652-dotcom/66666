#!/usr/bin/env python3
"""JJayo3 S26 Compose layout fix; run after scripts/patch_jjayo3_shell.py.
Maintain safe system insets, shrink keypad, preserve all buttons and native key events.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1])
path=root/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
s=path.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(s.count(old),old)
    s=s.replace(old,new,1)

replace('import androidx.compose.foundation.layout.Arrangement\n',
'''import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
''')
replace('''        Box(modifier = Modifier.fillMaxSize()) {
            Column(modifier = Modifier.fillMaxSize().background(Color(0xFF202020))) {''',
'''        // Android 15/16/17 edge-to-edge: keep the entire game + all buttons
        // inside the status/navigation bar safe area. Do not draw below navbar.
        Box(modifier = Modifier.fillMaxSize()
            .background(Color(0xFF202020))
            .windowInsetsPadding(WindowInsets.safeDrawing)) {
            Column(modifier = Modifier.fillMaxSize()) {''')
replace('''Keypad(hapticsEnabled = settings.keypadHaptics, modifier = Modifier.fillMaxWidth().padding(8.dp))''',
        '''Keypad(hapticsEnabled = settings.keypadHaptics, modifier = Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 4.dp))''')
replace('''Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {''',
        '''Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(2.dp)) {''')
replace('''Row(horizontalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.fillMaxWidth()) {''',
        '''Row(horizontalArrangement = Arrangement.spacedBy(3.dp), modifier = Modifier.fillMaxWidth()) {''')
replace('''.height(44.dp)
            .background(Color(0xFF404040)''',
        '''.height(40.dp)
            .background(Color(0xFF404040)''')
path.write_text(s)

# Bump version so newer build is unambiguously identified as an update.
gradle=root/"android/app/build.gradle.kts"
data=gradle.read_text()
assert data.count("versionCode = 5  // 매 업로드 증가 필요")==1
data=data.replace("versionCode = 5  // 매 업로드 증가 필요","versionCode = 6  // S26 screen-inset and graphics fix",1)
gradle.write_text(data)
print("Patched Android window safeDrawing inset and compact 7x3 keyboard without hiding keys.")

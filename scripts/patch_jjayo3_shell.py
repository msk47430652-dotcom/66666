#!/usr/bin/env python3
"""Prepare a game-free JJayo Tycoon 3 Android shell. Game bytes are inserted locally after build.
Only open-source host app sources are changed in the public workflow.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
base = root / 'android/app/src/main'

def edit(relative, old, new):
    path = root / relative
    content = path.read_text(encoding='utf8')
    assert content.count(old) == 1, f'{relative}: expected one match, found {content.count(old)}'
    path.write_text(content.replace(old, new, 1), encoding='utf8')

assets = base / 'assets'
assets.mkdir(parents=True, exist_ok=True)
(assets / 'jjayo3.zip').write_bytes(b'')
(assets / 'jjayo3_cover.png').write_bytes(b'')

activity = 'android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt'
edit(activity,
     'import kotlinx.coroutines.delay\n',
     'import androidx.compose.runtime.withFrameNanos\n'
     'import kotlinx.coroutines.Dispatchers\n'
     'import kotlinx.coroutines.withContext\n')
edit(activity,
     '        haptics = Haptics(this)\n\n        setContent {',
     '        haptics = Haptics(this)\n        ensureBundledGame()\n\n        setContent {')

bundle = '''    /** Import the original game supplied in the private, locally repackaged APK. */
    private fun ensureBundledGame() {
        runCatching {
            val directory = File(filesDir, "games/jjayo3").apply { mkdirs() }
            val gameFile = File(directory, "jjayo3.zip")
            if (!gameFile.isFile || gameFile.length() == 0L) {
                val temporary = File(directory, "jjayo3.zip.tmp")
                assets.open("jjayo3.zip").use { input ->
                    temporary.outputStream().use { output -> input.copyTo(output) }
                }
                if (temporary.length() == 0L) {
                    temporary.delete()
                    return@runCatching
                }
                if (!temporary.renameTo(gameFile)) {
                    temporary.copyTo(gameFile, overwrite = true)
                    temporary.delete()
                }
            }
            val cover = File(directory, "cover.png")
            if (!cover.isFile || cover.length() == 0L) {
                assets.open("jjayo3_cover.png").use { input ->
                    cover.outputStream().use { output -> input.copyTo(output) }
                }
                if (cover.length() == 0L) cover.delete()
            }
            val metadata = File(directory, "meta.json")
            if (!metadata.isFile) {
                metadata.writeText(org.json.JSONObject()
                    .put("name", "짜요짜요타이쿤3")
                    .put("filename", "jjayo3.zip")
                    .toString())
            }
        }.onFailure { android.util.Log.e("JJayo3", "Game import failed", it) }
    }

'''
edit(activity, '    override fun onDestroy() {', bundle + '    override fun onDestroy() {')

autostart = '''        // Load game and the 32 MB MIDI soundfont off the UI thread.
        LaunchedEffect(Unit) {
            val bundled = games.firstOrNull { it.id == "jjayo3" }
            if (bundled != null) {
                val started = runCatching {
                    withContext(Dispatchers.IO) {
                        bundled.dataDir.mkdirs()
                        start(bundled.gameFile.readBytes(), bundled.filename, bundled.dataDir)
                    }
                }.getOrDefault(false)
                if (started) {
                    errorMessage = null
                    screen = Screen.Emulator
                } else {
                    errorMessage = pendingError() ?: getString(R.string.error_start_failed)
                }
            }
        }

'''
edit(activity, '        emulatorActive = screen == Screen.Emulator',
     autostart + '        emulatorActive = screen == Screen.Emulator')
edit(activity, '                delay(16)',
     '                withFrameNanos { /* Vsync-paced, up to display refresh rate */ }')

edit(activity,
     '                        if (hapticsEnabled) view.performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY)\n'
     '                        WipiNative.nativeKeyDown(key)',
     '                        WipiNative.nativeKeyDown(key)\n'
     '                        if (hapticsEnabled) view.performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY)')

edit('android/app/build.gradle.kts',
     'applicationId = "com.parkjeongseop.wipi"',
     'applicationId = "com.jjayo3.s26"')
edit('android/app/build.gradle.kts',
     'abiFilters += listOf("arm64-v8a", "x86_64")',
     'abiFilters += listOf("arm64-v8a")')
edit('android/app/src/main/AndroidManifest.xml',
     'android:name=".MainActivity"',
     'android:name="com.parkjeongseop.wipi.MainActivity"')
for f in (base / 'res').glob('values*/strings.xml'):
    data = f.read_text(encoding='utf8')
    data, count = re.subn(r'<string name="app_name">[^<]*</string>',
                          '<string name="app_name">짜요짜요 타이쿤3</string>', data)
    assert count == 1, f'Cannot rewrite label {f}'
    f.write_text(data, encoding='utf8')

print('Public Android shell patched: arm64, auto-load, vsync, early input dispatch')
print('No game data included. Insert jjayo3.zip and cover in APK offline, then zipalign/sign.')

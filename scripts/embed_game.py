#!/usr/bin/env python3
"""Create a WIPI Android launcher with an empty asset slot that can be populated offline."""
from pathlib import Path
import shutil
import re
import zipfile
import sys

root = Path(sys.argv[1])
game = Path("game/wildfrontier.zip")
base = root / "android/app/src/main"
assets = base / "assets"
assets.mkdir(parents=True, exist_ok=True)
destination = assets / "wildfrontier.zip"
if game.exists():
    with zipfile.ZipFile(game) as z:
        assert z.testzip() is None, "Original ZIP CRC check failed"
        assert "0002CB52.jar" in z.namelist(), "Unexpected original game layout"
        with zipfile.ZipFile(z.open("0002CB52.jar")) as jar:
            assert jar.testzip() is None and "binary.mod" in jar.namelist()
    shutil.copyfile(game, destination)
    print("Included game in private build")
else:
    destination.write_bytes(b"")
    print("Public build: no game data included. Offline insertion slot created.")

source = base / "java/com/parkjeongseop/wipi/MainActivity.kt"
s = source.read_text()
anchor = r'(?m)^(\s*var showSettings by remember \{ mutableStateOf\(false\) \}[^\n]*\n)'
assert len(re.findall(anchor, s)) == 1, "Upstream WipiApp structure changed"
block = """
        // In a private build the bundled archive is loaded automatically.
        // The empty placeholder in a public build leaves the normal game library accessible.
        LaunchedEffect(Unit) {
            try {
                val bytes = assets.open("wildfrontier.zip").use { it.readBytes() }
                if (bytes.isNotEmpty()) {
                    val saveDir = File(filesDir, "wildfrontier_save").apply { mkdirs() }
                    if (start(bytes, "wildfrontier.zip", saveDir)) {
                        errorMessage = null
                        screen = Screen.Emulator
                    } else {
                        errorMessage = pendingError() ?: getString(R.string.error_start_failed)
                    }
                }
            } catch (e: Exception) {
                errorMessage = "Wild Frontier: " + (e.message ?: "Load failed")
            }
        }
"""
source.write_text(re.sub(anchor, lambda m: m.group(1)+block, s, count=1))
gradle = root / "android/app/build.gradle.kts"
g = gradle.read_text()
assert 'applicationId = "com.parkjeongseop.wipi"' in g
assert 'abiFilters += listOf("arm64-v8a", "x86_64")' in g
gradle.write_text(g.replace('applicationId = "com.parkjeongseop.wipi"', 'applicationId = "org.wildfrontier.personal"').replace('abiFilters += listOf("arm64-v8a", "x86_64")', 'abiFilters += listOf("arm64-v8a")'))
for f in (base / "res").glob("values*/strings.xml"):
    text = f.read_text()
    f.write_text(re.sub(r'<string name="app_name">[^<]+</string>', '<string name="app_name">와일드프론티어</string>', text))
print("Launcher patched; ARM64 app ID and autostart configured")

#!/usr/bin/env python3
"""Embed user's locally supplied LGT WIPI archive into Android launcher."""
from pathlib import Path
import re, shutil, zipfile, sys
root = Path(sys.argv[1])
game = Path("game/wildfrontier.zip")
if not game.exists():
    print("Game missing: building emulator-only APK")
    sys.exit(0)
with zipfile.ZipFile(game) as z:
    assert z.testzip() is None
    assert "0002CB52.jar" in z.namelist()
    with zipfile.ZipFile(z.open("0002CB52.jar")) as jar:
        assert jar.testzip() is None and "binary.mod" in jar.namelist()
base = root / "android/app/src/main"
assets = base / "assets"
assets.mkdir(parents=True,exist_ok=True)
shutil.copyfile(game, assets / "wildfrontier.zip")
main = base / "java/com/parkjeongseop/wipi/MainActivity.kt"
s = main.read_text()
anchor = r'(?m)^(\s*var showSettings by remember \{ mutableStateOf\(false\) \}[^\n]*\n)'
assert len(re.findall(anchor,s)) == 1, "Upstream WipiApp structure changed"
block = """
        LaunchedEffect(Unit) {
            try {
                val saved = File(filesDir, "wildfrontier_save").apply { mkdirs() }
                val bytes = assets.open("wildfrontier.zip").use { it.readBytes() }
                if (start(bytes, "wildfrontier.zip", saved)) {
                    errorMessage = null
                    screen = Screen.Emulator
                } else {
                    errorMessage = pendingError() ?: getString(R.string.error_start_failed)
                }
            } catch (error: Exception) {
                errorMessage = "Wild Frontier: " + (error.message ?: "Failed to load")
            }
        }
"""
s=re.sub(anchor, lambda m:m.group(1)+block, s, count=1)
main.write_text(s)
gradle= root / "android/app/build.gradle.kts"
g=gradle.read_text()
assert 'applicationId = "com.parkjeongseop.wipi"' in g
gradle.write_text(g.replace('applicationId = "com.parkjeongseop.wipi"','applicationId = "org.wildfrontier.personal"').replace('abiFilters += listOf("arm64-v8a", "x86_64")','abiFilters += listOf("arm64-v8a")'))
for f in (base/"res").glob("values*/strings.xml"):
    v=f.read_text()
    f.write_text(re.sub(r'<string name="app_name">[^<]+</string>','<string name="app_name">와일드프론티어</string>',v))
print("Embedded game and configured auto start")

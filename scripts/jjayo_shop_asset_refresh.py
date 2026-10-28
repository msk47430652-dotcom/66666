#!/usr/bin/env python3
"""Update the already-installed bundled JJayo3 game only if the packaged archive differs.
Do not delete the game directory or touch its /data save directory.
Run after original 3 local launcher patches.
"""
from pathlib import Path
import sys
base=Path(sys.argv[1])
p=base/"android/app/src/main/java/com/parkjeongseop/wipi/MainActivity.kt"
s=p.read_text(encoding="utf-8")
old='''            if (!gameFile.isFile || gameFile.length() == 0L) {
                val temporary = File(directory, "jjayo3.zip.tmp")
                assets.open("jjayo3.zip").use { input ->
                    temporary.outputStream().use { output -> input.copyTo(output) }
                }'''
new='''            // Update the embedded game when this APK contains a newer version.
            // This affects only games/jjayo3/jjayo3.zip. The separate 'data'
            // directory containing game saves is never removed or overwritten.
            val bundledGame = assets.open("jjayo3.zip").use { it.readBytes() }
            if (bundledGame.isNotEmpty() &&
                (!gameFile.isFile || !gameFile.readBytes().contentEquals(bundledGame))
            ) {
                val temporary = File(directory, "jjayo3.zip.tmp")
                temporary.writeBytes(bundledGame)'''
assert s.count(old)==1, f"Expected original bundled-game import block once, found {s.count(old)}"
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
p=base/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count("versionCode = 7")==1, "Expected name-input version 7"
s=s.replace("versionCode = 7","versionCode = 8",1)
p.write_text(s,encoding="utf-8")
print("Bundled asset refresh enabled: compare content and update only game ZIP. Save data untouched.")

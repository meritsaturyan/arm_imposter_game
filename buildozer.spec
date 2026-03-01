[app]
title = Arm Imposter
package.name = armimposter
package.domain = org.armimposter
source.dir = .
source.include_exts = py,png,jpg,jpeg,JPG,kv,json,txt
source.exclude_dirs = .venv,.git,.kivy,__pycache__,build
version = 1.0
requirements = python3,kivy,android
orientation = portrait
fullscreen = 0

# Assets
source.include_patterns = assets/*,data/*

# Icons (replace with your icon)
# icon.filename = assets/icon.png
# presplash.filename = assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1

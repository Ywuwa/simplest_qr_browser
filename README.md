## General info

This is a study pet-project, simple QR-scanner.

## Python files

+ **main.py** - main file which contains build-update functionality
+ **handle_camera** - switch camera functionality
+ **handle_scanning** - QR-code scanning logic, URL-displaying
+ **buildozer_optimization.py** - code that change buildozer.spec file (which is created after "buidozer init" command


## APK-file

Ready-to-go APK-file


## Sequence how to build APK in terminal
1. buildozer init
1. buildozer_optimization.py
1. buildozer -v android debug

> some additional sudo apt installs could be required



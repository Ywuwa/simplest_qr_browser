def update_spec():
    with open('buildozer.spec', 'r') as f:
        lines = f.readlines()

    with open('buildozer.spec', 'w') as f:
        for line in lines:
            if line.startswith('requirements ='):
                f.write('requirements = python3,kivy==2.3.0,pillow,pyzbar,libzbar,hostpython3\n')
            elif line.startswith('android.permissions ='):
                f.write('android.permissions = CAMERA, INTERNET\n')
            elif line.startswith('android.api ='):
                f.write('android.api = 33\n')
            elif line.startswith('#android.accept_sdk_license ='):
                f.write('android.accept_sdk_license = True\n')
            elif line.startswith('orientation ='):
                f.write('orientation = portrait\n')
            elif line.startswith('presplash.filename ='):
                f.write('presplash.filename = %(source.dir)s/icon.png\n')
            elif line.startswith('icon.filename ='):
                f.write('icon.filename = %(source.dir)s/icon.png\n')
            elif line.startswith('android.manifest.intent_filters ='):
                f.write('android.manifest.intent_filters = android.hardware.camera.autofocus')
            else:
                f.write(line)

def optimize_spec():
    with open('buildozer.spec', 'r') as f:
        lines = f.readlines()
    with open('buildozer.spec', 'w') as f:
        for line in lines:
            if line.startswith('android.archs ='):
                f.write('android.archs = arm64-v8a\n')
            elif line.startswith('android.p4a_blacklist ='):
                f.write('android.p4a_blacklist = sqlite3,openssl,http,ftplib,smtplib,pydoc,bz2,curses,decimal,enum34,telnetlib,unicodedata\n')
            else:
                f.write(line)

optimize_spec()
print("Оптимизация завершена. Можно запускать сборку.")
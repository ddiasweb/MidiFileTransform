import PyInstaller.__main__ as pyi

def install():
    pyi.run([
        'MidiFileTransform/main.py',
        '--name=MidiFileTransform',
        '--onefile',
        '--windowed'
    ])
import zipfile, struct, shutil

jar_path = r'E:\IDEA2024\idea2024\open36\Open436\hoj-judge-app.jar'
target = 'BOOT-INF/classes/top/hcode/hoj/judge/SandboxRun.class'

replacements = [
    (b'http://localhost:5050/file/{0}', b'http://judgehost:5050/file/{0}'),
    (b'http://localhost:5050', b'http://judgehost:5050'),
]

with zipfile.ZipFile(jar_path, 'r') as zin:
    data = bytearray(zin.read(target))
    for old_url, new_url in replacements:
        assert len(new_url) == len(old_url)
        pos = data.find(old_url)
        if pos == -1:
            print(f'{old_url} not found (already patched?)')
            continue
        print(f'Found {old_url} at offset {pos}')
        data[pos:pos+len(old_url)] = new_url

    new_jar = jar_path + '.patched'
    with zipfile.ZipFile(new_jar, 'w') as zout:
        for item in zin.infolist():
            if item.filename == target:
                zout.writestr(item, bytes(data))
            else:
                zout.writestr(item, zin.read(item.filename))

shutil.move(new_jar, jar_path)
print(f'Patched: {old_url} -> {new_url}')

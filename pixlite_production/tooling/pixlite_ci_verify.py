from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text()

# This marker is deliberately visible in phone-test builds. It makes it
# impossible to mistake a newly generated APK for an older installed build.
marker = 'PDF & Document Tools • TEST 24'
s = s.replace('PDF & Document Tools • TEST 24', marker)
s = s.replace('PDF & Document Tools', marker, 1)
p.write_text(s)

# Do not allow CI to produce an APK unless the features we expect were
# actually injected into the source that Flutter is about to compile.
required = {
    'persistent output model': 'class SavedOutput {',
    'persistent output store': 'class OutputStore {',
    'tool output persistence': 'OutputStore.saveBytes',
    'real Files screen': 'FutureBuilder<List<SavedOutput>>',
    'scanner bottom banner': "bottomAd:const CollapsibleBannerAdBox()",
    'scanner top banner': "BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolTopBanner)",
    'QR persistence': "'pixlite-qr.png','PNG'",
    'visible build marker': marker,
}

missing = [name for name, token in required.items() if token not in s]
if missing:
    print('CI VERIFICATION FAILED. Missing required PixLite changes:')
    for item in missing:
        print(' -', item)
    raise SystemExit(1)

print('PIXlITE TEST 24 SOURCE VERIFICATION PASSED')
for name in required:
    print(' OK:', name)
print(' marker:', marker)
print(' main.dart bytes:', p.stat().st_size)

from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text()

# TEST 25 must be unmistakable on-device and must keep the agreed Home ad
# inventory visibly reserved even if a live AdMob request temporarily returns
# no-fill. TEST 24 collapsed failed slots completely, which made the Home look
# as if the placements did not exist.
s = s.replace('PDF & Document Tools • TEST 24', 'PDF & Document Tools • TEST 25')
if 'PDF & Document Tools • TEST 25' not in s:
    s = s.replace('PDF & Document Tools', 'PDF & Document Tools • TEST 25', 1)
s = s.replace("    if(failed)return const SizedBox.shrink();\n", "")
p.write_text(s)

required = {
    'in-app PixLite icon': "Image.asset('assets/pixlite_icon.png'",
    'Home top banner': 'AdIds.homeTopBanner',
    'Home inline banner': 'AdIds.homeInlineBanner',
    'Home bottom banner': 'AdIds.homeBottomBanner',
    'persistent output model': 'class SavedOutput {',
    'persistent output store': 'class OutputStore {',
    'tool output persistence': 'OutputStore.saveBytes',
    'real Files screen': 'FutureBuilder<List<SavedOutput>>',
    'scanner bottom banner': "bottomAd:const CollapsibleBannerAdBox()",
    'scanner top banner': "BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolTopBanner)",
    'QR persistence': "'pixlite-qr.png','PNG'",
    'visible TEST 25 marker': 'PDF & Document Tools • TEST 25',
}

missing = [name for name, token in required.items() if token not in s]
if missing:
    print('CI VERIFICATION FAILED. Missing required PixLite TEST 25 changes:')
    for item in missing:
        print(' -', item)
    raise SystemExit(1)

print('PIXLITE TEST 25 SOURCE VERIFICATION PASSED')
for name in required:
    print(' OK:', name)
print(' main.dart bytes:', p.stat().st_size)

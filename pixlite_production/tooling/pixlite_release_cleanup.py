from pathlib import Path

p=Path('lib/main.dart')
s=p.read_text()

# Remove every user-visible TEST marker from the release candidate.
s=s.replace('PDF & Document Tools • TEST 34','PDF & Document Tools')
s=s.replace('PDF & Document Tools • TEST 33','PDF & Document Tools')
s=s.replace('PDF & Document Tools • TEST 32','PDF & Document Tools')
s=s.replace('PDF & Document Tools • TEST 31','PDF & Document Tools')
s=s.replace('PDF & Document Tools • TEST 30','PDF & Document Tools')

# Fail closed if any TEST marker remains in the Dart source.
if 'TEST ' in s:
    raise SystemExit('Release cleanup failed: TEST marker still present in lib/main.dart')

for q in ['PDF & Document Tools','Press back again to exit','PrivacyScreen(lang:lang,tr:tr)','SystemNavigator.pop()']:
    if q not in s:
        raise SystemExit('Release cleanup missing expected feature: '+q)

p.write_text(s)
print('PixLite release cleanup applied: no TEST marker remains.')

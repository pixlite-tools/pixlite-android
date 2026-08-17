from pathlib import Path
p=Path('lib/main.dart')
s=p.read_text()
s=s.replace('PDF & Document Tools • TEST 28','PDF & Document Tools • TEST 29')
if 'PDF & Document Tools • TEST 29' not in s:
    raise SystemExit('TEST 29 marker missing')
p.write_text(s)
print('PixLite TEST 29 marker applied.')

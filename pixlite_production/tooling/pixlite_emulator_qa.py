from pathlib import Path
import re, os
p=Path('lib/main.dart')
s=p.read_text()
s=s.replace("Future<void> main() async {","const bool pixliteQa = bool.fromEnvironment('PIXLITE_QA', defaultValue: false);\n\nFuture<void> main() async {",1)
s=s.replace('MobileAds.instance.initialize();','if (!pixliteQa) MobileAds.instance.initialize();')
s=s.replace('void _loadAd(){','void _loadAd(){\n    if (pixliteQa) return;')
s=s.replace('static void preload(){','static void preload(){\n    if (pixliteQa) return;')
s=re.sub(r"ca-app-pub-\d+/\d+","ca-app-pub-3940256099942544/6300978111",s)
s=s.replace("successInterstitial = 'ca-app-pub-3940256099942544/6300978111'","successInterstitial = 'ca-app-pub-3940256099942544/1033173712'")
s+=r'''
// QA-only entry point to the real processing/local-output functions, not picker/scan/share UI.
Future<Map<String,dynamic>> runPixLiteSyntheticQa(Directory output) async {
  if (!pixliteQa) throw StateError('QA build flag required');
  await output.create(recursive:true);
  final wide=img.Image(width:640,height:360);
  img.fill(wide,color:img.ColorRgb8(220,235,245));
  img.drawRect(wide,x1:4,y1:4,x2:635,y2:355,color:img.ColorRgb8(0,0,0),thickness:5);
  final tall=img.Image(width:360,height:640);
  img.fill(tall,color:img.ColorRgb8(240,225,205));
  img.drawRect(tall,x1:4,y1:4,x2:355,y2:635,color:img.ColorRgb8(0,0,0),thickness:5);
  final wideBytes=Uint8List.fromList(img.encodePng(wide));
  final tallBytes=Uint8List.fromList(img.encodePng(tall));
  final compressed=_compressImage(wideBytes,70);
  final resized=_resizeImage(wideBytes,320,180);
  final decoded=img.decodeImage(resized);
  if(decoded==null || decoded.width!=320 || decoded.height!=180) throw StateError('Resize dimensions wrong');
  var rejected=false;
  try {_compressImage(Uint8List.fromList([0,1,2,3]),70);} catch (_) {rejected=true;}
  if(!rejected) throw StateError('Invalid image accepted');
  final pdf=await _mergeImagesToPdf([wideBytes,tallBytes]);
  if(String.fromCharCodes(pdf.take(5))!='%PDF-') throw StateError('Missing PDF header');
  await File(output.path+'/synthetic-two-page.pdf').writeAsBytes(pdf,flush:true);
  await File(output.path+'/compressed.jpg').writeAsBytes(compressed,flush:true);
  await File(output.path+'/resized.jpg').writeAsBytes(resized,flush:true);
  final saved=await OutputStore.saveBytes(pdf,'qa-synthetic.pdf','PDF');
  final history=await OutputStore.list();
  if(!history.any((row)=>row.path==saved.path) || !await File(saved.path).exists()) throw StateError('Saved PDF missing');
  final result=<String,dynamic>{'synthetic_data':true,'real_app_processing':true,
    'resized_width':decoded.width,'resized_height':decoded.height,'invalid_image_rejected':rejected,
    'pdf_bytes':pdf.length,'history_persisted':true,'native_picker_tested':false,
    'native_scanner_tested':false,'received_share_tested':false};
  await File(output.path+'/processing.json').writeAsString(jsonEncode(result));
  return result;
}
'''
p.write_text(s)
spec=Path('pubspec.yaml').read_text().replace('dev_dependencies:\n','dev_dependencies:\n  integration_test:\n    sdk: flutter\n',1)
Path('pubspec.yaml').write_text(spec)
run=os.environ['GITHUB_RUN_NUMBER']
assert re.fullmatch(r'[1-9][0-9]{0,8}',run)
root=Path('android/app');kts=root/'build.gradle.kts'
txt=kts.read_text().replace('applicationId = "com.atlasova.pixlite"',f'applicationId = "com.atlasova.pixlite.qa.r{run}"')
assert f'applicationId = "com.atlasova.pixlite.qa.r{run}"' in txt
kts.write_text(txt)
manifest=root/'src/main/AndroidManifest.xml'
txt=manifest.read_text().replace('android:label="PixLite"',f'android:label="PixLite QA {run}"')
txt=re.sub(r'ca-app-pub-\d+~\d+','ca-app-pub-3940256099942544~3347511713',txt)
manifest.write_text(txt)
print('Isolated QA identity/test IDs configured; ad requests disabled by explicit QA flag.')

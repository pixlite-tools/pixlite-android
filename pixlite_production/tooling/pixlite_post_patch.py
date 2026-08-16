from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text()

# ---------------------------------------------------------------------------
# Localization / branding additions
# ---------------------------------------------------------------------------
additions = {
  'en': "'home':'Home','files':'Files','settings':'Settings','home_hero1':'PDF tools.','home_hero2':'Fast and simple.','home_hero_sub':'Convert • Merge • Compress','scan_document':'Scan document','quick_tools':'Quick Tools','my_files':'My Files','recent':'Recent','all':'All','recent_scans':'Your generated files will appear here','file_history':'Files created with PixLite are stored on your device.','language':'Language','theme':'Theme','dark':'Dark','privacy':'Privacy','on_device':'On-device','clear_cache':'Clear cache'",
  'ar': "'home':'الرئيسية','files':'الملفات','settings':'الإعدادات','home_hero1':'أدوات PDF.','home_hero2':'سريعة وبسيطة.','home_hero_sub':'تحويل • دمج • ضغط','scan_document':'مسح مستند','quick_tools':'أدوات سريعة','my_files':'ملفاتي','recent':'الأخيرة','all':'الكل','recent_scans':'ستظهر الملفات التي أنشأتها هنا','file_history':'الملفات التي ينشئها PixLite محفوظة على جهازك.','language':'اللغة','theme':'المظهر','dark':'داكن','privacy':'الخصوصية','on_device':'على الجهاز','clear_cache':'مسح التخزين المؤقت'",
  'fr': "'home':'Accueil','files':'Fichiers','settings':'Réglages','home_hero1':'Outils PDF.','home_hero2':'Rapides et simples.','home_hero_sub':'Convertir • Fusionner • Compresser','scan_document':'Scanner un document','quick_tools':'Outils rapides','my_files':'Mes fichiers','recent':'Récents','all':'Tous','recent_scans':'Vos fichiers créés apparaîtront ici','file_history':'Les fichiers créés avec PixLite sont stockés sur votre appareil.','language':'Langue','theme':'Thème','dark':'Sombre','privacy':'Confidentialité','on_device':'Sur l’appareil','clear_cache':'Vider le cache'",
  'es': "'home':'Inicio','files':'Archivos','settings':'Ajustes','home_hero1':'Herramientas PDF.','home_hero2':'Rápidas y simples.','home_hero_sub':'Convertir • Combinar • Comprimir','scan_document':'Escanear documento','quick_tools':'Herramientas rápidas','my_files':'Mis archivos','recent':'Recientes','all':'Todo','recent_scans':'Tus archivos creados aparecerán aquí','file_history':'Los archivos creados con PixLite se guardan en tu dispositivo.','language':'Idioma','theme':'Tema','dark':'Oscuro','privacy':'Privacidad','on_device':'En el dispositivo','clear_cache':'Limpiar caché'",
}
markers = {
  'en': "'ad':'Advertisement','after_result_ad':'Ad after result','before':'Before','after':'After'",
  'ar': "'ad':'إعلان','after_result_ad':'إعلان بعد النتيجة','before':'قبل','after':'بعد'",
  'fr': "'ad':'Publicité','after_result_ad':'Pub après résultat','before':'Avant','after':'Après'",
  'es': "'ad':'Anuncio','after_result_ad':'Anuncio después','before':'Antes','after':'Después'",
}
for lang, marker in markers.items():
  start = s.find(f"'{lang}': {{")
  if start != -1 and "'home_hero1'" not in s[start:start+3000]:
    s = s.replace(marker, marker + ',' + additions[lang])

# Branded header with icon + subtitle.
header_re = r"Row\(children:\[const Expanded\(child:Text\('PixLite',style:TextStyle\(color:kText,fontSize:27,fontWeight:FontWeight\.w900,letterSpacing:-1\)\)\),PopupMenuButton"
header_new = "Row(children:[Expanded(child:Row(children:[Image.asset('assets/pixlite_icon.png',width:36,height:36),const SizedBox(width:10),const Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('PixLite',style:TextStyle(color:kText,fontSize:27,fontWeight:FontWeight.w900,letterSpacing:-1)),SizedBox(height:1),Text('PDF & Document Tools',style:TextStyle(color:kSub,fontSize:10.5,fontWeight:FontWeight.w700,letterSpacing:.2))])])),PopupMenuButton"
s = re.sub(header_re, header_new, s, count=1)

# Fully localize Home hero and nav labels.
s = s.replace("const Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('PDF tools.'", "Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(tr('home_hero1')")
s = s.replace("Text('Fast and simple.'", "Text(tr('home_hero2')")
s = s.replace("Text('Convert • Merge • Compress'", "Text(tr('home_hero_sub')")
s = s.replace("label:const Text('Create PDF'", "label:Text(tr('create_pdf')")
s = s.replace("label:const Text('Scan document'", "label:Text(tr('scan_document')")
s = s.replace("const Text('Quick Tools'", "Text(tr('quick_tools')")
s = s.replace("destinations:const [", "destinations:[")
s = s.replace("label:'Home'", "label:widget.tr('home')")
s = s.replace("label:'Files'", "label:widget.tr('files')")
s = s.replace("label:'Settings'", "label:widget.tr('settings')")

# ---------------------------------------------------------------------------
# Persistent output history
# ---------------------------------------------------------------------------
if "import 'dart:convert';" not in s:
  s = s.replace("import 'dart:io';", "import 'dart:convert';\nimport 'dart:io';", 1)

store_code = r'''
class SavedOutput {
  final String name,path,kind;
  final int createdAt,size;
  const SavedOutput({required this.name,required this.path,required this.kind,required this.createdAt,required this.size});
  Map<String,dynamic> toJson()=>{'name':name,'path':path,'kind':kind,'createdAt':createdAt,'size':size};
  static SavedOutput? fromJson(String raw){
    try{
      final m=jsonDecode(raw) as Map<String,dynamic>;
      return SavedOutput(name:m['name']??'',path:m['path']??'',kind:m['kind']??'',createdAt:m['createdAt']??0,size:m['size']??0);
    }catch(_){return null;}
  }
}

class OutputStore {
  static const _key='pixlite_outputs_v1';
  static Future<Directory> _dir() async{
    final root=await getApplicationDocumentsDirectory();
    final dir=Directory('${root.path}/PixLite');
    if(!await dir.exists()) await dir.create(recursive:true);
    return dir;
  }
  static String _uniqueName(String name){
    final dot=name.lastIndexOf('.');
    final stamp=DateTime.now().millisecondsSinceEpoch;
    if(dot<1)return '${name}_$stamp';
    return '${name.substring(0,dot)}_$stamp${name.substring(dot)}';
  }
  static Future<SavedOutput> saveBytes(Uint8List bytes,String name,String kind) async{
    final dir=await _dir();
    final file=File('${dir.path}/${_uniqueName(name)}');
    await file.writeAsBytes(bytes,flush:true);
    final item=SavedOutput(name:file.uri.pathSegments.last,path:file.path,kind:kind,createdAt:DateTime.now().millisecondsSinceEpoch,size:bytes.length);
    final prefs=await SharedPreferences.getInstance();
    final rows=prefs.getStringList(_key)??<String>[];
    rows.insert(0,jsonEncode(item.toJson()));
    if(rows.length>100) rows.removeRange(100,rows.length);
    await prefs.setStringList(_key,rows);
    return item;
  }
  static Future<List<SavedOutput>> list() async{
    final prefs=await SharedPreferences.getInstance();
    final rows=prefs.getStringList(_key)??<String>[];
    final out=<SavedOutput>[];
    final clean=<String>[];
    for(final raw in rows){
      final item=SavedOutput.fromJson(raw);
      if(item!=null && await File(item.path).exists()){
        out.add(item); clean.add(raw);
      }
    }
    if(clean.length!=rows.length) await prefs.setStringList(_key,clean);
    out.sort((a,b)=>b.createdAt.compareTo(a.createdAt));
    return out;
  }
  static Future<void> clear() async{
    final items=await list();
    for(final item in items){try{await File(item.path).delete();}catch(_){}}
    final prefs=await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
'''
if 'class SavedOutput {' not in s:
  s = s.replace('class InterstitialAdManager {', store_code + '\nclass InterstitialAdManager {', 1)

# Save successful tool results immediately, while keeping existing share flow.
s = s.replace(
  "final result=_compressImage(data,(quality*100).round()); if(!mounted)return; setState(()=>output=result); showMsg('Image compressed successfully');",
  "final result=_compressImage(data,(quality*100).round()); await OutputStore.saveBytes(result,'pixlite-compressed.jpg','JPG'); if(!mounted)return; setState(()=>output=result); showMsg('Image compressed successfully');"
)
s = s.replace(
  "final result=_resizeImage(data,nw.clamp(1,10000),nh.clamp(1,10000)); if(!mounted)return; setState(()=>output=result); showMsg('Image resized successfully');",
  "final result=_resizeImage(data,nw.clamp(1,10000),nh.clamp(1,10000)); await OutputStore.saveBytes(result,'pixlite-resized.jpg','JPG'); if(!mounted)return; setState(()=>output=result); showMsg('Image resized successfully');"
)
s = s.replace(
  "final pdfBytes=await _mergeImagesToPdf([data]); if(!mounted)return; setState(()=>output=pdfBytes); showMsg('PDF created successfully');",
  "final pdfBytes=await _mergeImagesToPdf([data]); await OutputStore.saveBytes(pdfBytes,'pixlite.pdf','PDF'); if(!mounted)return; setState(()=>output=pdfBytes); showMsg('PDF created successfully');"
)
s = s.replace(
  "final result=await _mergeImagesToPdf(images);\n      if(!mounted)return;\n      setState(()=>output=result);",
  "final result=await _mergeImagesToPdf(images);\n      await OutputStore.saveBytes(result,'pixlite-merged.pdf','PDF');\n      if(!mounted)return;\n      setState(()=>output=result);"
)

# Save scanner pages when a scan succeeds and save generated scan PDF before sharing.
s = s.replace(
  "for(final p in images){\n        await _normalizeImageOrientation(p);\n      }",
  "for(int i=0;i<images.length;i++){\n        final p=images[i];\n        await _normalizeImageOrientation(p);\n        try{await OutputStore.saveBytes(await File(p).readAsBytes(),'pixlite-scan-${i+1}.jpg','JPG');}catch(_){}\n      }"
)
s = s.replace(
  "await file.writeAsBytes(pdfBytes,flush:true);\n      await Share.shareXFiles([XFile(file.path)]);",
  "await file.writeAsBytes(pdfBytes,flush:true);\n      await OutputStore.saveBytes(pdfBytes,'pixlite-scan.pdf','PDF');\n      await Share.shareXFiles([XFile(file.path)]);",
  1
)

# Save QR image to PixLite history when the user exports it.
s = s.replace(
  "await file.writeAsBytes(data.buffer.asUint8List(),flush:true); await Share.shareXFiles([XFile(file.path)]);",
  "final bytes=data.buffer.asUint8List(); await file.writeAsBytes(bytes,flush:true); await OutputStore.saveBytes(bytes,'pixlite-qr.png','PNG'); await Share.shareXFiles([XFile(file.path)]);"
)

# ---------------------------------------------------------------------------
# Files + Settings screens
# ---------------------------------------------------------------------------
s = s.replace("home(),const FilesScreen(),SettingsScreen(lang:widget.lang,onLang:widget.onLang)", "home(),FilesScreen(tr:widget.tr),SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr)")
s = s.replace("home(),FilesScreen(tr:widget.tr),SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr)", "home(),FilesScreen(tr:widget.tr),SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr)")

files_block = r"class FilesScreen extends StatelessWidget\{.*?\n\}\nclass SettingsScreen"
files_new = r'''class FilesScreen extends StatelessWidget{
  final String Function(String) tr;
  const FilesScreen({super.key, required this.tr});
  String sizeText(int n){ if(n<1024)return '$n B'; if(n<1024*1024)return '${(n/1024).toStringAsFixed(0)} KB'; return '${(n/(1024*1024)).toStringAsFixed(1)} MB'; }
  IconData iconFor(String kind)=>kind=='PDF'?Icons.picture_as_pdf_rounded:kind=='PNG'?Icons.qr_code_2_rounded:Icons.image_rounded;
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.fromLTRB(16,18,16,26),children:[
    Text(tr('my_files'),style:const TextStyle(color:kText,fontSize:25,fontWeight:FontWeight.w900)),
    const SizedBox(height:12),
    BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolTopBanner),
    const SizedBox(height:14),
    FutureBuilder<List<SavedOutput>>(
      future:OutputStore.list(),
      builder:(context,snap){
        if(snap.connectionState==ConnectionState.waiting)return const Padding(padding:EdgeInsets.all(28),child:Center(child:CircularProgressIndicator()));
        final items=snap.data??const <SavedOutput>[];
        if(items.isEmpty)return Container(padding:const EdgeInsets.symmetric(vertical:50,horizontal:22),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(22),border:Border.all(color:kStroke)),child:Column(children:[const Icon(Icons.folder_open_rounded,color:kSub,size:50),const SizedBox(height:12),Text(tr('recent_scans'),style:const TextStyle(color:kText,fontWeight:FontWeight.w900)),const SizedBox(height:6),Text(tr('file_history'),textAlign:TextAlign.center,style:const TextStyle(color:kSub,fontSize:11))]));
        return Column(children:items.map((item)=>Container(
          margin:const EdgeInsets.only(bottom:9),padding:const EdgeInsets.symmetric(horizontal:12,vertical:10),
          decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(16),border:Border.all(color:kStroke)),
          child:Row(children:[
            Container(width:42,height:42,decoration:BoxDecoration(color:kViolet.withOpacity(.14),borderRadius:BorderRadius.circular(12)),child:Icon(iconFor(item.kind),color:kViolet,size:22)),
            const SizedBox(width:11),
            Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(item.name,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(color:kText,fontSize:12,fontWeight:FontWeight.w900)),const SizedBox(height:3),Text('${item.kind} • ${sizeText(item.size)}',style:const TextStyle(color:kSub,fontSize:10))])),
            IconButton(onPressed:()=>Share.shareXFiles([XFile(item.path)]),icon:const Icon(Icons.ios_share_rounded,color:kSub,size:20))
          ])
        )).toList());
      }
    ),
    const SizedBox(height:12),
    CollapsibleBannerAdBox(),
  ]);
}
class SettingsScreen'''
s = re.sub(files_block, files_new, s, count=1, flags=re.S)

settings_block = r"class SettingsScreen extends StatelessWidget\{.*?\n\}\nclass _SettingTile"
settings_new = r'''class SettingsScreen extends StatelessWidget{
  final String lang; final Future<void> Function(String) onLang; final String Function(String) tr;
  const SettingsScreen({super.key,required this.lang,required this.onLang,required this.tr});
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.fromLTRB(16,18,16,26),children:[
    Text(tr('settings'),style:const TextStyle(color:kText,fontSize:25,fontWeight:FontWeight.w900)),
    const SizedBox(height:12),
    BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolTopBanner),
    const SizedBox(height:16),
    _SettingTile(icon:Icons.language_rounded,title:tr('language'),value:langNames[lang]??lang,onTap:()=>showModalBottomSheet(context:context,backgroundColor:kCard2,builder:(c)=>SafeArea(child:Column(mainAxisSize:MainAxisSize.min,children:langNames.entries.map((e)=>ListTile(title:Text(e.value,style:const TextStyle(color:kText)),trailing:e.key==lang?const Icon(Icons.check_rounded,color:kViolet):null,onTap:(){Navigator.pop(c);onLang(e.key);})).toList())))),
    _SettingTile(icon:Icons.dark_mode_rounded,title:tr('theme'),value:tr('dark')),
    _SettingTile(icon:Icons.lock_outline_rounded,title:tr('privacy'),value:tr('on_device')),
    _SettingTile(icon:Icons.cleaning_services_rounded,title:tr('clear_cache'),value:'',onTap:()async{await OutputStore.clear();if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('PixLite file history cleared')));}),
    const SizedBox(height:16),
    CollapsibleBannerAdBox(),
  ]);
}
class _SettingTile'''
s = re.sub(settings_block, settings_new, s, count=1, flags=re.S)

p.write_text(s)
print('PixLite post-patch applied: localization, branding, persistent Files history, ads.')

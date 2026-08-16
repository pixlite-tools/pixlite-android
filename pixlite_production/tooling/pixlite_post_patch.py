from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text()

additions = {
  'en': "'home':'Home','files':'Files','settings':'Settings','home_hero1':'PDF tools.','home_hero2':'Fast and simple.','home_hero_sub':'Convert • Merge • Compress','scan_document':'Scan document','quick_tools':'Quick Tools','my_files':'My Files','recent':'Recent','all':'All','recent_scans':'Recent scans will appear here','file_history':'File history will be connected after the scan workflow is finalized.','language':'Language','theme':'Theme','dark':'Dark','privacy':'Privacy','on_device':'On-device','clear_cache':'Clear cache'",
  'ar': "'home':'الرئيسية','files':'الملفات','settings':'الإعدادات','home_hero1':'أدوات PDF.','home_hero2':'سريعة وبسيطة.','home_hero_sub':'تحويل • دمج • ضغط','scan_document':'مسح مستند','quick_tools':'أدوات سريعة','my_files':'ملفاتي','recent':'الأخيرة','all':'الكل','recent_scans':'ستظهر الملفات هنا','file_history':'سيتم ربط سجل الملفات بعد اكتمال مسار الحفظ.','language':'اللغة','theme':'المظهر','dark':'داكن','privacy':'الخصوصية','on_device':'على الجهاز','clear_cache':'مسح التخزين المؤقت'",
  'fr': "'home':'Accueil','files':'Fichiers','settings':'Réglages','home_hero1':'Outils PDF.','home_hero2':'Rapides et simples.','home_hero_sub':'Convertir • Fusionner • Compresser','scan_document':'Scanner un document','quick_tools':'Outils rapides','my_files':'Mes fichiers','recent':'Récents','all':'Tous','recent_scans':'Les fichiers récents apparaîtront ici','file_history':'L’historique des fichiers sera connecté après finalisation du flux.','language':'Langue','theme':'Thème','dark':'Sombre','privacy':'Confidentialité','on_device':'Sur l’appareil','clear_cache':'Vider le cache'",
  'es': "'home':'Inicio','files':'Archivos','settings':'Ajustes','home_hero1':'Herramientas PDF.','home_hero2':'Rápidas y simples.','home_hero_sub':'Convertir • Combinar • Comprimir','scan_document':'Escanear documento','quick_tools':'Herramientas rápidas','my_files':'Mis archivos','recent':'Recientes','all':'Todo','recent_scans':'Los archivos recientes aparecerán aquí','file_history':'El historial se conectará después de finalizar el flujo.','language':'Idioma','theme':'Tema','dark':'Oscuro','privacy':'Privacidad','on_device':'En el dispositivo','clear_cache':'Limpiar caché'",
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

# Wire translation and ads into Files/Settings.
s = s.replace("home(),const FilesScreen(),SettingsScreen(lang:widget.lang,onLang:widget.onLang)", "home(),FilesScreen(tr:widget.tr),SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr)")

files_block = r"class FilesScreen extends StatelessWidget\{.*?\n\}\nclass SettingsScreen"
files_new = r"""class FilesScreen extends StatelessWidget{
  final String Function(String) tr;
  const FilesScreen({super.key, required this.tr});
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.fromLTRB(16,18,16,26),children:[
    Text(tr('my_files'),style:const TextStyle(color:kText,fontSize:25,fontWeight:FontWeight.w900)),
    const SizedBox(height:12),
    BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolTopBanner),
    const SizedBox(height:12),
    Row(children:[tr('recent'),'PDF','JPG',tr('all')].map((t)=>Padding(padding:const EdgeInsetsDirectional.only(end:8),child:Container(padding:const EdgeInsets.symmetric(horizontal:13,vertical:8),decoration:BoxDecoration(color:t==tr('recent')?kViolet.withOpacity(.18):kCard,borderRadius:BorderRadius.circular(99),border:Border.all(color:t==tr('recent')?kViolet:kStroke)),child:Text(t,style:TextStyle(color:t==tr('recent')?Colors.white:kSub,fontSize:11,fontWeight:FontWeight.w800))))).toList()),
    const SizedBox(height:16),
    Container(padding:const EdgeInsets.symmetric(vertical:58,horizontal:22),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(22),border:Border.all(color:kStroke)),child:Column(children:[const Icon(Icons.folder_open_rounded,color:kSub,size:50),const SizedBox(height:12),Text(tr('recent_scans'),style:const TextStyle(color:kText,fontWeight:FontWeight.w900)),const SizedBox(height:6),Text(tr('file_history'),textAlign:TextAlign.center,style:const TextStyle(color:kSub,fontSize:11))])),
    const SizedBox(height:16),
    CollapsibleBannerAdBox(),
  ]);
}
class SettingsScreen"""
s = re.sub(files_block, files_new, s, count=1, flags=re.S)

settings_block = r"class SettingsScreen extends StatelessWidget\{.*?\n\}\nclass _SettingTile"
settings_new = r"""class SettingsScreen extends StatelessWidget{
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
    _SettingTile(icon:Icons.cleaning_services_rounded,title:tr('clear_cache'),value:''),
    const SizedBox(height:16),
    CollapsibleBannerAdBox(),
  ]);
}
class _SettingTile"""
s = re.sub(settings_block, settings_new, s, count=1, flags=re.S)

p.write_text(s)
print('PixLite post-patch applied: localization, branding, Files/Settings ads.')

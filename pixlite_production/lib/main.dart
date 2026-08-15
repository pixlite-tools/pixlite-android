
import 'dart:io';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:google_mlkit_document_scanner/google_mlkit_document_scanner.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PixLiteBootstrap());
  // Deferred to after the first frame so it can never delay the home screen
  // from appearing -- ads/services never gate app startup.
  WidgetsBinding.instance.addPostFrameCallback((_) {
    MobileAds.instance.initialize();
  });
}

class PixLiteBootstrap extends StatefulWidget {
  const PixLiteBootstrap({super.key});
  @override State<PixLiteBootstrap> createState() => _PixLiteBootstrapState();
}

class _PixLiteBootstrapState extends State<PixLiteBootstrap> {
  String lang = 'en';
  @override void initState(){
    super.initState();
    _loadPrefs();
  }
  Future<void> _loadPrefs() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('lang');
      if(saved != null && mounted) setState(() => lang = saved);
    } catch (_) {}
  }
  @override Widget build(BuildContext context) => PixLiteApp(initialLang: lang, key: ValueKey(lang));
}

const kBg = Color(0xFF050814);
const kCard = Color(0xFF0D1324);
const kCard2 = Color(0xFF121A30);
const kStroke = Color(0xFF26304C);
const kText = Color(0xFFF6F7FF);
const kSub = Color(0xFFA6ABC4);
const kViolet = Color(0xFF8A3FFC);
const kBlue = Color(0xFF149BFF);
const kMint = Color(0xFF37E8B4);
const kGold = Color(0xFFFFC857);
const kPink = Color(0xFFFF5E98);

const langNames = {'en':'English','ar':'العربية','fr':'Français','es':'Español'};

class L {
  static final Map<String, Map<String, String>> s = {
    'en': {
      'tag':'SMART FILE TOOLS','hero':'Make files lighter,\ncleaner and ready.','hero_sub':'Compress, resize, scan, convert and create QR codes with a clean workflow.',
      'services':'Services','compress':'Compress','compress_sub':'Reduce image size','resize':'Resize','resize_sub':'Change dimensions','scan':'Scan','scan_sub':'Clean document photos',
      'pdf':'Image to PDF','pdf_sub':'Create a PDF file','merge':'Merge','merge_sub':'Images to one PDF','qr':'QR Code','qr_sub':'Generate QR locally','gallery':'Gallery','camera':'Camera','quality':'Quality','process':'Process',
      'save_share':'Save / Share','width':'Width','height':'Height','keep_ratio':'Keep ratio','create_pdf':'Create PDF','generate_qr':'Generate QR','text_link':'Text or link',
      'ad':'Advertisement','after_result_ad':'Ad after result','before':'Before','after':'After'
    },
    'ar': {
      'tag':'أدوات ملفات ذكية','hero':'خلّي ملفاتك أخف،\nأنظف وجاهزة.','hero_sub':'ضغط، تغيير أبعاد، مسح وثائق، تحويل PDF وإنشاء QR بتجربة بسيطة.',
      'services':'الخدمات','compress':'ضغط الصور','compress_sub':'تقليل حجم الصورة','resize':'تغيير الأبعاد','resize_sub':'تعديل العرض والطول','scan':'مسح المستند','scan_sub':'تنظيف صور الوثائق',
      'pdf':'صورة إلى PDF','pdf_sub':'إنشاء ملف PDF','merge':'دمج','merge_sub':'دمج الصور في PDF واحد','qr':'رمز QR','qr_sub':'إنشاء QR محليًا','gallery':'المعرض','camera':'الكاميرا','quality':'الجودة','process':'معالجة',
      'save_share':'حفظ / مشاركة','width':'العرض','height':'الطول','keep_ratio':'الحفاظ على النسبة','create_pdf':'إنشاء PDF','generate_qr':'إنشاء QR','text_link':'نص أو رابط',
      'ad':'إعلان','after_result_ad':'إعلان بعد النتيجة','before':'قبل','after':'بعد'
    },
    'fr': {
      'tag':'OUTILS DE FICHIERS','hero':'Rends tes fichiers\nplus légers et prêts.','hero_sub':'Compresser, redimensionner, scanner, convertir en PDF et créer un QR.',
      'services':'Services','compress':'Compresser','compress_sub':'Réduire la taille','resize':'Redimensionner','resize_sub':'Changer les dimensions','scan':'Scanner','scan_sub':'Nettoyer les documents',
      'pdf':'Image en PDF','pdf_sub':'Créer un fichier PDF','merge':'Fusionner','merge_sub':'Fusionner des images en PDF','qr':'Code QR','qr_sub':'Créer un QR local','gallery':'Galerie','camera':'Caméra','quality':'Qualité','process':'Traiter',
      'save_share':'Enregistrer / Partager','width':'Largeur','height':'Hauteur','keep_ratio':'Garder le ratio','create_pdf':'Créer PDF','generate_qr':'Créer QR','text_link':'Texte ou lien',
      'ad':'Publicité','after_result_ad':'Pub après résultat','before':'Avant','after':'Après'
    },
    'es': {
      'tag':'HERRAMIENTAS SMART','hero':'Archivos más ligeros,\nlimpios y listos.','hero_sub':'Comprime, redimensiona, escanea, convierte a PDF y crea QR.',
      'services':'Servicios','compress':'Comprimir','compress_sub':'Reducir tamaño','resize':'Redimensionar','resize_sub':'Cambiar dimensiones','scan':'Escanear','scan_sub':'Limpiar documentos',
      'pdf':'Imagen a PDF','pdf_sub':'Crear PDF','merge':'Combinar','merge_sub':'Combinar imágenes en un PDF','qr':'Código QR','qr_sub':'Crear QR local','gallery':'Galería','camera':'Cámara','quality':'Calidad','process':'Procesar',
      'save_share':'Guardar / Compartir','width':'Ancho','height':'Alto','keep_ratio':'Mantener ratio','create_pdf':'Crear PDF','generate_qr':'Crear QR','text_link':'Texto o enlace',
      'ad':'Anuncio','after_result_ad':'Anuncio después','before':'Antes','after':'Después'
    }
  };
}

class PixLiteApp extends StatefulWidget {
  final String initialLang;
  const PixLiteApp({super.key, required this.initialLang});
  @override State<PixLiteApp> createState() => _PixLiteAppState();
}

class _PixLiteAppState extends State<PixLiteApp> {
  late String lang;
  @override void initState(){ super.initState(); lang = widget.initialLang; }
  Future<void> setLang(String v) async { final p = await SharedPreferences.getInstance(); await p.setString('lang', v); setState(() => lang = v); }
  String tr(String k) => L.s[lang]?[k] ?? L.s['en']![k] ?? k;
  @override Widget build(BuildContext context) {
    return Directionality(
      textDirection: lang == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: MaterialApp(
        title:'PixLite', debugShowCheckedModeBanner:false,
        theme: ThemeData(
          useMaterial3:true, scaffoldBackgroundColor:kBg, colorScheme: ColorScheme.fromSeed(seedColor:kViolet, brightness:Brightness.dark),
          appBarTheme: const AppBarTheme(backgroundColor:kBg, surfaceTintColor:Colors.transparent, foregroundColor:kText),
          filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(backgroundColor:kViolet, foregroundColor:Colors.white, minimumSize: const Size.fromHeight(54), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)))),
          outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(foregroundColor:kText, side: const BorderSide(color:kStroke), minimumSize: const Size.fromHeight(48), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)))),
          inputDecorationTheme: InputDecorationTheme(filled:true, fillColor:kCard2, labelStyle: const TextStyle(color:kSub), border: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kStroke)), enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kStroke)), focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kViolet))),
        ),
        home: HomeScreen(lang: lang, tr: tr, onLang: setLang),
      ),
    );
  }
}

class AdIds {
  static String get banner => Platform.isAndroid ? 'ca-app-pub-3940256099942544/6300978111' : 'ca-app-pub-3940256099942544/2934735716';
}

class BannerAdBox extends StatefulWidget {
  final String label; final bool large;
  const BannerAdBox({super.key,required this.label,this.large=false});
  @override State<BannerAdBox> createState()=>_BannerAdBoxState();
}
class _BannerAdBoxState extends State<BannerAdBox>{
  BannerAd? ad; bool loaded=false;
  @override void initState(){
    super.initState();
    // Ad objects are created only after the first frame is up, so the home
    // screen is never gated on an ad network round-trip.
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadAd());
  }
  void _loadAd(){
    if(!mounted) return;
    final size=widget.large?AdSize.largeBanner:AdSize.banner;
    ad=BannerAd(size:size,adUnitId:AdIds.banner,listener:BannerAdListener(onAdLoaded:(_){if(mounted)setState(()=>loaded=true);},onAdFailedToLoad:(a,e)=>a.dispose()),request:const AdRequest())..load();
  }
  @override void dispose(){ad?.dispose();super.dispose();}
  @override Widget build(BuildContext context)=>Container(height:widget.large?110:60,alignment:Alignment.center,decoration:BoxDecoration(color:const Color(0xFF090F1E),border:Border.all(color:kStroke),borderRadius:BorderRadius.circular(18)),child:loaded&&ad!=null?SizedBox(width:ad!.size.width.toDouble(),height:ad!.size.height.toDouble(),child:AdWidget(ad:ad!)):Row(mainAxisAlignment:MainAxisAlignment.center,children:[const Icon(Icons.ads_click_rounded,color:kSub,size:17),const SizedBox(width:7),Text(widget.label.toUpperCase(),style:const TextStyle(color:kSub,fontSize:10,letterSpacing:1))]));
}

class HomeScreen extends StatefulWidget{
  final String lang; final String Function(String) tr; final Future<void> Function(String) onLang;
  const HomeScreen({super.key,required this.lang,required this.tr,required this.onLang});
  @override State<HomeScreen> createState()=>_HomeScreenState();
}
class _HomeScreenState extends State<HomeScreen>{
  int tab=0;
  void open(Widget p)=>Navigator.push(context,MaterialPageRoute(builder:(_)=>p));
  Widget home(){
    final tr=widget.tr;
    final quick=[
      ToolData(tr('pdf'),tr('pdf_sub'),Icons.picture_as_pdf_rounded,kPink,ImageToPdfScreen(tr:tr)),
      ToolData(tr('merge'),tr('merge_sub'),Icons.layers_rounded,kMint,MergeScreen(tr:tr)),
      ToolData(tr('compress'),tr('compress_sub'),Icons.compress_rounded,const Color(0xFF9DFF00),CompressScreen(tr:tr)),
      ToolData(tr('resize'),tr('resize_sub'),Icons.crop_free_rounded,kBlue,ResizeScreen(tr:tr)),
      ToolData(tr('scan'),tr('scan_sub'),Icons.document_scanner_rounded,kViolet,ScanScreen(tr:tr)),
      ToolData(tr('qr'),tr('qr_sub'),Icons.qr_code_2_rounded,const Color(0xFF726BFF),QrScreen(tr:tr)),
    ];
    return ListView(padding:const EdgeInsets.fromLTRB(16,10,16,22),children:[
      Row(children:[const Expanded(child:Text('PixLite',style:TextStyle(color:kText,fontSize:27,fontWeight:FontWeight.w900,letterSpacing:-1))),PopupMenuButton<String>(initialValue:widget.lang,color:kCard2,onSelected:widget.onLang,itemBuilder:(_)=>langNames.entries.map((e)=>PopupMenuItem(value:e.key,child:Text(e.value))).toList(),child:Container(padding:const EdgeInsets.symmetric(horizontal:12,vertical:9),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(14),border:Border.all(color:kStroke)),child:Row(mainAxisSize:MainAxisSize.min,children:[Text(widget.lang.toUpperCase(),style:const TextStyle(color:kText,fontSize:12,fontWeight:FontWeight.w800)),const Icon(Icons.keyboard_arrow_down_rounded,color:kSub,size:17)]))) ]),
      const SizedBox(height:12),
      BannerAdBox(label:tr('ad')),
      const SizedBox(height:12),
      Container(padding:const EdgeInsets.all(18),decoration:BoxDecoration(borderRadius:BorderRadius.circular(26),border:Border.all(color:const Color(0x667C4DFF)),gradient:const LinearGradient(colors:[Color(0xFF181044),Color(0xFF2B1674),Color(0xFF053D72)],begin:Alignment.topLeft,end:Alignment.bottomRight),boxShadow:const [BoxShadow(color:Color(0x553E2BFF),blurRadius:30,offset:Offset(0,12))]),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Row(children:[Container(width:58,height:58,decoration:BoxDecoration(borderRadius:BorderRadius.circular(18),gradient:const LinearGradient(colors:[Color(0xFFBC2FFF),Color(0xFF2A6BFF)])),child:const Icon(Icons.picture_as_pdf_rounded,color:Colors.white,size:31)),const SizedBox(width:14),const Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('PDF tools.',style:TextStyle(color:Colors.white,fontSize:24,fontWeight:FontWeight.w900,height:1)),SizedBox(height:4),Text('Fast and simple.',style:TextStyle(color:Colors.white,fontSize:24,fontWeight:FontWeight.w900,height:1)),SizedBox(height:8),Text('Convert • Merge • Compress',style:TextStyle(color:Color(0xFFD5DAFF),fontSize:11.5))]))]),
        const SizedBox(height:18),
        Container(decoration:BoxDecoration(gradient:const LinearGradient(colors:[Color(0xFFC72EF3),Color(0xFF6D35FF),Color(0xFF009CF6)]),borderRadius:BorderRadius.circular(16),boxShadow:const [BoxShadow(color:Color(0x553C7CFF),blurRadius:18)]),child:FilledButton.icon(onPressed:()=>open(ImageToPdfScreen(tr:tr)),style:FilledButton.styleFrom(backgroundColor:Colors.transparent,shadowColor:Colors.transparent,minimumSize:const Size.fromHeight(56)),icon:const Icon(Icons.picture_as_pdf_rounded),label:const Text('Create PDF',style:TextStyle(fontWeight:FontWeight.w900)))),
        const SizedBox(height:10),OutlinedButton.icon(onPressed:()=>open(ScanScreen(tr:tr)),icon:const Icon(Icons.document_scanner_rounded),label:const Text('Scan document',style:TextStyle(fontWeight:FontWeight.w800)))
      ])),
      const SizedBox(height:18),const Text('Quick Tools',style:TextStyle(color:kText,fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:10),
      GridView.builder(itemCount:quick.length,shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),gridDelegate:const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount:2,crossAxisSpacing:10,mainAxisSpacing:10,childAspectRatio:1.8),itemBuilder:(c,i){final t=quick[i];return InkWell(borderRadius:BorderRadius.circular(18),onTap:()=>open(t.page),child:Container(padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(18),border:Border.all(color:kStroke)),child:Row(children:[Container(width:42,height:42,decoration:BoxDecoration(color:t.color.withOpacity(.13),borderRadius:BorderRadius.circular(13)),child:Icon(t.icon,color:t.color,size:23)),const SizedBox(width:10),Expanded(child:Column(mainAxisAlignment:MainAxisAlignment.center,crossAxisAlignment:CrossAxisAlignment.start,children:[Text(t.title,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(color:kText,fontSize:12.5,fontWeight:FontWeight.w900)),const SizedBox(height:3),Text(t.subtitle,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(color:kSub,fontSize:9.5))]))])));}),
      const SizedBox(height:12),BannerAdBox(label:tr('ad'),large:true),const SizedBox(height:12),
      Container(padding:const EdgeInsets.all(13),decoration:BoxDecoration(color:const Color(0xFF0A1121),borderRadius:BorderRadius.circular(17),border:Border.all(color:const Color(0x3337E8B4))),child:const Row(children:[Icon(Icons.shield_outlined,color:kMint,size:21),SizedBox(width:9),Expanded(child:Text('Private by design • Files stay on your device',style:TextStyle(color:kSub,fontSize:11,fontWeight:FontWeight.w700)))])),
    ]);
  }
  @override Widget build(BuildContext context)=>Scaffold(
    body:SafeArea(child:IndexedStack(index:tab,children:[home(),const FilesScreen(),SettingsScreen(lang:widget.lang,onLang:widget.onLang)])),
    bottomNavigationBar:Column(mainAxisSize:MainAxisSize.min,children:[
      // Anchored above the nav bar, visible on Home only -- Files/Settings
      // stay ad-free rather than carrying an ad onto every screen.
      if(tab==0) Padding(padding:const EdgeInsets.fromLTRB(12,8,12,0),child:BannerAdBox(label:widget.tr('ad'))),
      NavigationBar(height:70,backgroundColor:const Color(0xFF080D19),indicatorColor:kViolet.withOpacity(.22),selectedIndex:tab,onDestinationSelected:(i)=>setState(()=>tab=i),destinations:const [NavigationDestination(icon:Icon(Icons.home_outlined),selectedIcon:Icon(Icons.home_rounded),label:'Home'),NavigationDestination(icon:Icon(Icons.folder_outlined),selectedIcon:Icon(Icons.folder_rounded),label:'Files'),NavigationDestination(icon:Icon(Icons.settings_outlined),selectedIcon:Icon(Icons.settings_rounded),label:'Settings')]),
    ]),
  );
}
class FilesScreen extends StatelessWidget{
  const FilesScreen({super.key});
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.fromLTRB(16,18,16,26),children:[const Text('My Files',style:TextStyle(color:kText,fontSize:25,fontWeight:FontWeight.w900)),const SizedBox(height:12),Row(children:['Recent','PDF','JPG','All'].map((t)=>Padding(padding:const EdgeInsetsDirectional.only(end:8),child:Container(padding:const EdgeInsets.symmetric(horizontal:13,vertical:8),decoration:BoxDecoration(color:t=='Recent'?kViolet.withOpacity(.18):kCard,borderRadius:BorderRadius.circular(99),border:Border.all(color:t=='Recent'?kViolet:kStroke)),child:Text(t,style:TextStyle(color:t=='Recent'?Colors.white:kSub,fontSize:11,fontWeight:FontWeight.w800))))).toList()),const SizedBox(height:16),Container(padding:const EdgeInsets.symmetric(vertical:58,horizontal:22),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(22),border:Border.all(color:kStroke)),child:const Column(children:[Icon(Icons.folder_open_rounded,color:kSub,size:50),SizedBox(height:12),Text('Recent scans will appear here',style:TextStyle(color:kText,fontWeight:FontWeight.w900)),SizedBox(height:6),Text('File history will be connected after the scan workflow is finalized.',textAlign:TextAlign.center,style:TextStyle(color:kSub,fontSize:11))]))]);
}
class SettingsScreen extends StatelessWidget{
  final String lang; final Future<void> Function(String) onLang;
  const SettingsScreen({super.key,required this.lang,required this.onLang});
  @override Widget build(BuildContext context)=>ListView(padding:const EdgeInsets.fromLTRB(16,18,16,26),children:[const Text('Settings',style:TextStyle(color:kText,fontSize:25,fontWeight:FontWeight.w900)),const SizedBox(height:16),_SettingTile(icon:Icons.language_rounded,title:'Language',value:langNames[lang]??lang,onTap:()=>showModalBottomSheet(context:context,backgroundColor:kCard2,builder:(c)=>SafeArea(child:Column(mainAxisSize:MainAxisSize.min,children:langNames.entries.map((e)=>ListTile(title:Text(e.value,style:const TextStyle(color:kText)),trailing:e.key==lang?const Icon(Icons.check_rounded,color:kViolet):null,onTap:(){Navigator.pop(c);onLang(e.key);})).toList())))),const _SettingTile(icon:Icons.dark_mode_rounded,title:'Theme',value:'Dark'),const _SettingTile(icon:Icons.lock_outline_rounded,title:'Privacy',value:'On-device'),const _SettingTile(icon:Icons.cleaning_services_rounded,title:'Clear cache',value:'')]);
}
class _SettingTile extends StatelessWidget{final IconData icon;final String title,value;final VoidCallback? onTap;const _SettingTile({required this.icon,required this.title,required this.value,this.onTap});@override Widget build(BuildContext context)=>Container(margin:const EdgeInsets.only(bottom:9),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(16),border:Border.all(color:kStroke)),child:ListTile(onTap:onTap,leading:Icon(icon,color:kSub),title:Text(title,style:const TextStyle(color:kText,fontSize:12.5,fontWeight:FontWeight.w800)),trailing:Row(mainAxisSize:MainAxisSize.min,children:[if(value.isNotEmpty)Text(value,style:const TextStyle(color:kSub,fontSize:11)),const SizedBox(width:4),const Icon(Icons.chevron_right_rounded,color:kSub,size:19)])));
}

class MiniPill extends StatelessWidget{ final String text; final Color color; const MiniPill(this.text,this.color,{super.key}); @override Widget build(BuildContext context)=>Container(padding: const EdgeInsets.symmetric(horizontal:11,vertical:7), decoration:BoxDecoration(color:color.withOpacity(.12),borderRadius:BorderRadius.circular(99),border:Border.all(color:color.withOpacity(.35))), child:Text(text,style:TextStyle(color:color,fontSize:10,fontWeight:FontWeight.w900))); }
class ToolData { final String title,subtitle; final IconData icon; final Color color; final Widget page; const ToolData(this.title,this.subtitle,this.icon,this.color,this.page); }

class ToolShell extends StatelessWidget { final String title; final Widget child; const ToolShell({super.key, required this.title, required this.child}); @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:Text(title,style: const TextStyle(fontWeight:FontWeight.w900))), body:SafeArea(child:ListView(padding: const EdgeInsets.fromLTRB(18,8,18,26),children:[child]))); }
class CardBox extends StatelessWidget{ final Widget child; const CardBox({super.key, required this.child}); @override Widget build(BuildContext context)=>Container(padding: const EdgeInsets.all(15), decoration:BoxDecoration(color:kCard,border:Border.all(color:kStroke),borderRadius:BorderRadius.circular(24)), child:child); }

abstract class ImageToolState<T extends StatefulWidget> extends State<T> {
  final picker=ImagePicker(); Uint8List? input; Uint8List? output; bool busy=false;
  Future<void> choose(ImageSource source) async { try{ final file=await picker.pickImage(source:source,imageQuality:100); if(file==null)return; final bytes=await file.readAsBytes(); setState((){input=bytes; output=null;}); } catch(_){ showMsg('Could not open image'); } }
  Future<void> shareBytes(Uint8List bytes,String name) async { final dir=await getTemporaryDirectory(); final file=File('${dir.path}/$name'); await file.writeAsBytes(bytes,flush:true); await Share.shareXFiles([XFile(file.path)]); }
  void showMsg(String msg){ if(!mounted)return; ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(msg))); }
}
class PickerPanel extends StatelessWidget { final String Function(String) tr; final Uint8List? bytes; final VoidCallback gallery,camera; const PickerPanel({super.key,required this.tr,this.bytes,required this.gallery,required this.camera}); @override Widget build(BuildContext context)=>CardBox(child:Column(children:[
  Container(height:260,width:double.infinity,decoration:BoxDecoration(color:kCard2,borderRadius:BorderRadius.circular(20),border:Border.all(color:kStroke)),clipBehavior:Clip.antiAlias,child:bytes==null?const Center(child:Icon(Icons.image_outlined,size:54,color:kSub)):Image.memory(bytes!,fit:BoxFit.contain)),
  const SizedBox(height:12), Row(children:[Expanded(child:OutlinedButton.icon(onPressed:gallery,icon: const Icon(Icons.photo_library_outlined),label:Text(tr('gallery')))), const SizedBox(width:8), Expanded(child:OutlinedButton.icon(onPressed:camera,icon: const Icon(Icons.photo_camera_outlined),label:Text(tr('camera'))))])
])); }
class ResultAd extends StatelessWidget { final bool show; final String label; const ResultAd({super.key,required this.show,required this.label}); @override Widget build(BuildContext context)=>show?Padding(padding: const EdgeInsets.only(top:14),child:BannerAdBox(label:label)): const SizedBox.shrink(); }

// ---------------------------------------------------------------------------
// Image/PDF processing helpers. These run synchronously on the main isolate
// (no compute()/background isolate) so they can never accidentally touch a
// Flutter plugin from a context without engine bindings -- decode/resize/PDF
// generation here is pure Dart (image + pdf packages) and fast enough at
// these resolutions that a short setState + frame yield keeps the busy
// indicator visible without a real isolate hop.
// ---------------------------------------------------------------------------

Uint8List _compressImage(Uint8List bytes,int quality){
  final decoded=img.decodeImage(bytes);
  if(decoded==null) throw Exception('Could not decode image');
  return Uint8List.fromList(img.encodeJpg(decoded,quality:quality));
}

Uint8List _resizeImage(Uint8List bytes,int width,int height){
  final decoded=img.decodeImage(bytes);
  if(decoded==null) throw Exception('Could not decode image');
  final resized=img.copyResize(decoded,width:width,height:height,interpolation:img.Interpolation.average);
  return Uint8List.fromList(img.encodeJpg(resized,quality:92));
}

Future<Uint8List> _mergeImagesToPdf(List<Uint8List> images) async {
  final doc=pw.Document();
  for(final bytes in images){
    final mem=pw.MemoryImage(bytes);
    doc.addPage(pw.Page(build:(_)=>pw.Center(child:pw.Image(mem,fit:pw.BoxFit.contain))));
  }
  return Uint8List.fromList(await doc.save());
}

// Flutter's Image.file (Skia's JPEG decoder) never applies the EXIF
// orientation tag -- it always shows the pixel grid exactly as stored. Some
// devices hand the document scanner a capture whose pixels are stored
// sideways with an EXIF orientation tag describing the correction, instead
// of physically rotated pixels. That looks fine in apps that read EXIF
// (Google Photos, the scanner's own review screen) but sideways/upside-down
// in PixLite's preview and in anything the raw file is later shared to.
// Baking the orientation into the pixels once, right after the scan result
// comes back, makes every consumer that touches this same file path
// (preview, share, save) see the same upright image. When the file is
// already upright (the common case), this is a no-op and never rewrites or
// recompresses it.
Future<void> _normalizeImageOrientation(String path) async {
  try {
    final file=File(path);
    final bytes=await file.readAsBytes();
    final decoded=img.decodeImage(bytes);
    if(decoded==null) return;
    final ifd=decoded.exif.imageIfd;
    if(!ifd.hasOrientation||ifd.orientation==1) return;
    final corrected=img.bakeOrientation(decoded);
    final reencoded=Uint8List.fromList(img.encodeJpg(corrected,quality:100));
    await file.writeAsBytes(reencoded,flush:true);
  }catch(_){
    // Leave the original scanned file untouched rather than risk losing it.
  }
}

class CompressScreen extends StatefulWidget { final String Function(String) tr; const CompressScreen({super.key,required this.tr}); @override State<CompressScreen> createState()=>_CompressScreenState(); }
class _CompressScreenState extends ImageToolState<CompressScreen>{ double quality=.82; Future<void> process() async{ final data=input; if(data==null)return; setState(()=>busy=true); await Future.delayed(const Duration(milliseconds:50)); try{ final result=_compressImage(data,(quality*100).round()); if(!mounted)return; setState(()=>output=result); showMsg('Image compressed successfully'); }catch(e){showMsg('Compress failed: $e');}finally{if(mounted)setState(()=>busy=false);} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('compress'), child:Column(children:[PickerPanel(tr:widget.tr,bytes:output??input,gallery:()=>choose(ImageSource.gallery),camera:()=>choose(ImageSource.camera)), if(input!=null)...[const SizedBox(height:12), CardBox(child:Column(children:[Row(children:[Text(widget.tr('quality'),style: const TextStyle(color:kText,fontWeight:FontWeight.w800)),const Spacer(),Text('${(quality*100).round()}%',style: const TextStyle(color:kSub))]), Slider(value:quality,min:.25,max:1,activeColor:kViolet,onChanged:(v)=>setState(()=>quality=v)), if(output!=null)Padding(padding: const EdgeInsets.only(bottom:8), child:Row(mainAxisAlignment:MainAxisAlignment.spaceBetween,children:[Text('${widget.tr('before')} ${(input!.length/1024).round()} KB',style: const TextStyle(fontSize:11,color:kSub)), Text('${widget.tr('after')} ${(output!.length/1024).round()} KB',style: const TextStyle(fontSize:11,fontWeight:FontWeight.w900,color:kMint))])), FilledButton(onPressed:busy?null:process,child:Text(busy?'...':widget.tr('process'))), if(output!=null)OutlinedButton(onPressed:()=>shareBytes(output!,'pixlite-compressed.jpg'),child:Text(widget.tr('save_share')))])), ResultAd(show:output!=null,label:widget.tr('after_result_ad'))]]));
}

class ResizeScreen extends StatefulWidget{ final String Function(String) tr; const ResizeScreen({super.key,required this.tr}); @override State<ResizeScreen> createState()=>_ResizeScreenState(); }
class _ResizeScreenState extends ImageToolState<ResizeScreen>{ final w=TextEditingController(); final h=TextEditingController(); double ratio=1; bool keepRatio=true; @override void dispose(){w.dispose();h.dispose();super.dispose();}
  @override Future<void> choose(ImageSource source) async{ await super.choose(source); final d=img.decodeImage(input??Uint8List(0)); if(d!=null){ ratio=d.width/d.height; w.text=d.width.toString(); h.text=d.height.toString(); setState((){}); } }
  void syncHeight(String value){ if(!keepRatio||ratio==0)return; final width=int.tryParse(value); if(width==null||width<1)return; h.text=(width/ratio).round().toString(); }
  Future<void> process() async{ final data=input; if(data==null)return; setState(()=>busy=true); await Future.delayed(const Duration(milliseconds:50)); try{ final nw=int.tryParse(w.text)??0; final nh=int.tryParse(h.text)??0; final result=_resizeImage(data,nw.clamp(1,10000),nh.clamp(1,10000)); if(!mounted)return; setState(()=>output=result); showMsg('Image resized successfully'); }catch(e){showMsg('Resize failed: $e');}finally{if(mounted)setState(()=>busy=false);} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('resize'), child:Column(children:[PickerPanel(tr:widget.tr,bytes:output??input,gallery:()=>choose(ImageSource.gallery),camera:()=>choose(ImageSource.camera)), if(input!=null)...[const SizedBox(height:12),CardBox(child:Column(children:[Row(children:[Expanded(child:TextField(controller:w,keyboardType:TextInputType.number,decoration:InputDecoration(labelText:widget.tr('width')),onChanged:syncHeight)),const SizedBox(width:8),Expanded(child:TextField(controller:h,keyboardType:TextInputType.number,decoration:InputDecoration(labelText:widget.tr('height'))))]), const SizedBox(height:8), SwitchListTile(contentPadding:EdgeInsets.zero,value:keepRatio,activeColor:kMint,onChanged:(v)=>setState(()=>keepRatio=v),title:Text(widget.tr('keep_ratio'),style: const TextStyle(color:kText,fontWeight:FontWeight.w700))), FilledButton(onPressed:busy?null:process,child:Text(busy?'...':widget.tr('process'))), if(output!=null)OutlinedButton(onPressed:()=>shareBytes(output!,'pixlite-resized.jpg'),child:Text(widget.tr('save_share')))])), ResultAd(show:output!=null,label:widget.tr('after_result_ad'))]]));
}




class ScanScreen extends StatefulWidget{
  final String Function(String) tr;
  const ScanScreen({super.key,required this.tr});
  @override State<ScanScreen> createState()=>_ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen>{
  final List<String> imagePaths=[];
  String? pdfPath;
  int? pdfPages;
  int pageIndex=0;
  bool busy=false;
  DocumentScanner? scanner;

  bool get hasImages=>imagePaths.isNotEmpty;
  bool get hasResult=>hasImages||pdfPath!=null;

  String _filePathFromUri(String uri){
    if(uri.startsWith('file://')) return Uri.parse(uri).toFilePath();
    return uri;
  }

  Future<void> startScan() async{
    if(busy)return;
    setState(()=>busy=true);
    try{
      const formats=<DocumentFormat>{DocumentFormat.jpeg,DocumentFormat.pdf};
      final options=DocumentScannerOptions(
        documentFormats:formats,
        mode:ScannerMode.full,
        pageLimit:10,
        isGalleryImport:true,
      );
      scanner=DocumentScanner(options:options);
      final result=await scanner!.scanDocument();
      final images=result.images??<String>[];
      final pdf=result.pdf;
      for(final p in images){
        await _normalizeImageOrientation(p);
      }
      if(!mounted)return;
      setState((){
        imagePaths..clear()..addAll(images);
        pdfPath=pdf==null?null:_filePathFromUri(pdf.uri);
        pdfPages=pdf?.pageCount;
        pageIndex=0;
      });
      if(images.isEmpty&&pdf==null){
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('No scanned document was returned.')));
      }
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Scanner failed: $e')));
    }finally{
      try{scanner?.close();}catch(_){}
      scanner=null;
      if(mounted)setState(()=>busy=false);
    }
  }

  Future<void> shareImages() async{
    if(imagePaths.isEmpty)return;
    await Share.shareXFiles(imagePaths.map((p)=>XFile(p)).toList());
  }
  Future<void> sharePdf() async{
    final p=pdfPath; if(p==null)return;
    await Share.shareXFiles([XFile(p)]);
  }
  void newScan(){setState((){imagePaths.clear();pdfPath=null;pdfPages=null;pageIndex=0;});}
  @override void dispose(){try{scanner?.close();}catch(_){} super.dispose();}

  @override Widget build(BuildContext context)=>ToolShell(
    title:widget.tr('scan'),
    child:Column(children:[
      CardBox(child:Column(children:[
        Container(
          height:390,width:double.infinity,
          decoration:BoxDecoration(
            color:const Color(0xFF070B15),borderRadius:BorderRadius.circular(22),
            border:Border.all(color:hasResult?kViolet:kStroke,width:hasResult?1.5:1),
            boxShadow:hasResult?[BoxShadow(color:kViolet.withOpacity(.12),blurRadius:24)]:null
          ),
          clipBehavior:Clip.antiAlias,
          child:busy
            ? const Column(mainAxisAlignment:MainAxisAlignment.center,children:[
                SizedBox(width:42,height:42,child:CircularProgressIndicator(strokeWidth:3)),
                SizedBox(height:16),
                Text('Opening scanner…',style:TextStyle(color:kText,fontWeight:FontWeight.w900)),
                SizedBox(height:6),
                Padding(padding:EdgeInsets.symmetric(horizontal:28),child:Text(
                  'The first launch may take longer while Google Play services prepares the scanner.',
                  textAlign:TextAlign.center,style:TextStyle(color:kSub,fontSize:11,height:1.4)))
              ])
            :hasImages
              ? Stack(children:[
                  PageView.builder(
                    itemCount:imagePaths.length,
                    onPageChanged:(i)=>setState(()=>pageIndex=i),
                    itemBuilder:(_,i)=>Padding(padding:const EdgeInsets.all(10),child:Image.file(File(imagePaths[i]),fit:BoxFit.contain,gaplessPlayback:true))
                  ),
                  Positioned(bottom:10,left:0,right:0,child:Center(child:Container(
                    padding:const EdgeInsets.symmetric(horizontal:10,vertical:5),
                    decoration:BoxDecoration(color:Colors.black.withOpacity(.70),borderRadius:BorderRadius.circular(99)),
                    child:Text('${pageIndex+1}/${imagePaths.length}',style:const TextStyle(color:Colors.white,fontSize:10,fontWeight:FontWeight.w900))
                  )))
                ])
              : const Column(mainAxisAlignment:MainAxisAlignment.center,children:[
                  Icon(Icons.document_scanner_rounded,size:80,color:kBlue),SizedBox(height:14),
                  Text('Document Scanner',style:TextStyle(color:kText,fontSize:18,fontWeight:FontWeight.w900)),
                  SizedBox(height:8),
                  Padding(padding:EdgeInsets.symmetric(horizontal:26),child:Text(
                    'Scan a document, adjust it if needed, then save it as an image or PDF.',
                    textAlign:TextAlign.center,style:TextStyle(color:kSub,fontSize:11.5,height:1.45)))
                ])
        ),
        if(hasImages)...[
          const SizedBox(height:10),
          Row(mainAxisAlignment:MainAxisAlignment.center,children:[
            const Icon(Icons.auto_awesome_rounded,color:kMint,size:17),const SizedBox(width:5),
            Text('${imagePaths.length} page(s) scanned',style:const TextStyle(color:kMint,fontSize:11,fontWeight:FontWeight.w900))
          ])
        ],
        const SizedBox(height:15),
        FilledButton.icon(
          onPressed:busy?null:startScan,
          icon:Icon(busy?Icons.hourglass_empty_rounded:Icons.document_scanner_rounded),
          label:Text(busy?'Opening scanner…':'Scan / Import document')
        ),
        if(hasResult)...[
          const SizedBox(height:12),
          Container(
            padding:const EdgeInsets.all(12),
            decoration:BoxDecoration(color:kCard2,borderRadius:BorderRadius.circular(18),border:Border.all(color:kStroke)),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              const Text('EXPORT',style:TextStyle(color:kSub,fontSize:10,fontWeight:FontWeight.w900,letterSpacing:1.1)),
              const SizedBox(height:9),
              if(hasImages)OutlinedButton.icon(onPressed:shareImages,icon:const Icon(Icons.image_outlined),label:const Text('Save / Share images')),
              if(pdfPath!=null)...[
                if(hasImages)const SizedBox(height:8),
                FilledButton.icon(
                  onPressed:sharePdf,icon:const Icon(Icons.picture_as_pdf_rounded),
                  label:Text(pdfPages==null?'Save / Share PDF':'Save / Share PDF • $pdfPages page(s)')
                ),
              ],
              const SizedBox(height:8),
              OutlinedButton.icon(onPressed:null,icon:const Icon(Icons.description_outlined),label:const Text('Word / OCR — next step'))
            ])
          ),
          const SizedBox(height:8),
          TextButton.icon(onPressed:newScan,icon:const Icon(Icons.refresh_rounded),label:const Text('New scan'))
        ]
      ])),
      ResultAd(show:hasResult,label:widget.tr('after_result_ad'))
    ])
  );
}


class ImageToPdfScreen extends StatefulWidget{ final String Function(String) tr; const ImageToPdfScreen({super.key,required this.tr}); @override State<ImageToPdfScreen> createState()=>_ImageToPdfScreenState(); }
class _ImageToPdfScreenState extends ImageToolState<ImageToPdfScreen>{ Future<void> process() async{ final data=input; if(data==null)return; setState(()=>busy=true); await Future.delayed(const Duration(milliseconds:50)); try{ final pdfBytes=await _mergeImagesToPdf([data]); if(!mounted)return; setState(()=>output=pdfBytes); showMsg('PDF created successfully'); }catch(e){showMsg('PDF creation failed: $e');}finally{if(mounted)setState(()=>busy=false);} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('pdf'), child:Column(children:[PickerPanel(tr:widget.tr,bytes:input,gallery:()=>choose(ImageSource.gallery),camera:()=>choose(ImageSource.camera)), if(input!=null)...[const SizedBox(height:12),CardBox(child:Column(children:[FilledButton(onPressed:busy?null:process,child:Text(busy?'...':widget.tr('create_pdf'))), if(output!=null)OutlinedButton(onPressed:()=>shareBytes(output!,'pixlite.pdf'),child:Text(widget.tr('save_share')))])), ResultAd(show:output!=null,label:widget.tr('after_result_ad'))]]));
}

class MergeScreen extends StatefulWidget{ final String Function(String) tr; const MergeScreen({super.key,required this.tr}); @override State<MergeScreen> createState()=>_MergeScreenState(); }
class _MergeScreenState extends State<MergeScreen>{
  final picker=ImagePicker();
  List<Uint8List> images=[];
  Uint8List? output;
  bool busy=false;

  Future<void> pickImages() async {
    try{
      final files=await picker.pickMultiImage(imageQuality:100);
      if(files.isEmpty) return;
      final bytesList = await Future.wait(files.map((f)=>f.readAsBytes()));
      setState((){ images=bytesList; output=null; });
    }catch(_){ showMsg('Could not open images'); }
  }

  Future<void> addFromCamera() async {
    try{
      final file=await picker.pickImage(source:ImageSource.camera,imageQuality:100);
      if(file==null) return;
      final bytes=await file.readAsBytes();
      setState((){ images=[...images,bytes]; output=null; });
    }catch(_){ showMsg('Could not capture image'); }
  }

  void clearAll(){ setState((){ images=[]; output=null; }); }

  Future<void> merge() async {
    if(images.isEmpty)return;
    setState(()=>busy=true);
    await Future.delayed(const Duration(milliseconds:50));
    try{
      final result=await _mergeImagesToPdf(images);
      if(!mounted)return;
      setState(()=>output=result);
      showMsg('PDF created successfully');
    }catch(e){ showMsg('Merge failed: $e'); }
    finally{ if(mounted) setState(()=>busy=false); }
  }

  Future<void> shareOutput() async {
    final data=output; if(data==null)return;
    final dir=await getTemporaryDirectory();
    final file=File('${dir.path}/pixlite-merged.pdf');
    await file.writeAsBytes(data,flush:true);
    await Share.shareXFiles([XFile(file.path)]);
  }

  void showMsg(String msg){ if(!mounted)return; ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(msg))); }

  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('merge'), child:Column(children:[
    CardBox(child:Column(children:[
      Container(height:120,width:double.infinity,alignment:Alignment.center,decoration:BoxDecoration(color:kCard2,borderRadius:BorderRadius.circular(20),border:Border.all(color:kStroke)),child:images.isEmpty?const Icon(Icons.layers_rounded,size:40,color:kSub):Text('${images.length} image(s) selected',style:const TextStyle(color:kText,fontWeight:FontWeight.w900))),
      const SizedBox(height:12),
      Row(children:[
        Expanded(child:OutlinedButton.icon(onPressed:pickImages,icon:const Icon(Icons.photo_library_outlined),label:Text(widget.tr('gallery')))),
        const SizedBox(width:8),
        Expanded(child:OutlinedButton.icon(onPressed:addFromCamera,icon:const Icon(Icons.photo_camera_outlined),label:Text(widget.tr('camera')))),
      ]),
      const SizedBox(height:12),
      FilledButton(onPressed:(busy||images.isEmpty)?null:merge,child:Text(busy?'...':widget.tr('merge'))),
      if(images.isNotEmpty)Padding(padding:const EdgeInsets.only(top:8),child:TextButton(onPressed:busy?null:clearAll,child:const Text('Clear'))),
      if(output!=null)OutlinedButton(onPressed:shareOutput,child:Text(widget.tr('save_share'))),
    ])),
    ResultAd(show:output!=null,label:widget.tr('after_result_ad'))
  ]));
}

class QrScreen extends StatefulWidget{ final String Function(String) tr; const QrScreen({super.key,required this.tr}); @override State<QrScreen> createState()=>_QrScreenState(); }
class _QrScreenState extends State<QrScreen>{ final ctrl=TextEditingController(); final qrKey=GlobalKey(); String value=''; @override void dispose(){ctrl.dispose(); super.dispose();}
  Future<void> shareQr() async{ try{ final boundary=qrKey.currentContext?.findRenderObject() as RenderRepaintBoundary?; if(boundary==null)return; final image=await boundary.toImage(pixelRatio:3); final data=await image.toByteData(format:ui.ImageByteFormat.png); if(data==null)return; final dir=await getTemporaryDirectory(); final file=File('${dir.path}/pixlite-qr.png'); await file.writeAsBytes(data.buffer.asUint8List(),flush:true); await Share.shareXFiles([XFile(file.path)]); }catch(_){} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('qr'), child:Column(children:[CardBox(child:Column(children:[TextField(controller:ctrl,decoration:InputDecoration(labelText:widget.tr('text_link'))), const SizedBox(height:14), FilledButton(onPressed:()=>setState(()=>value=ctrl.text.trim()),child:Text(widget.tr('generate_qr'))), if(value.isNotEmpty)...[const SizedBox(height:22), RepaintBoundary(key:qrKey,child:Container(padding: const EdgeInsets.all(18),decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(20)), child:QrImageView(data:value,version:QrVersions.auto,size:220))), const SizedBox(height:12), OutlinedButton(onPressed:shareQr,child:Text(widget.tr('save_share')))] ])), ResultAd(show:value.isNotEmpty,label:widget.tr('after_result_ad'))]));
}

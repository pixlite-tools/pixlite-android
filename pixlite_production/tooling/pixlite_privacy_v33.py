from pathlib import Path

p=Path('lib/main.dart')
s=p.read_text()

old="_SettingTile(icon:Icons.lock_outline_rounded,title:tr('privacy'),value:tr('on_device'))," 
new="_SettingTile(icon:Icons.lock_outline_rounded,title:tr('privacy'),value:tr('on_device'),onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>PrivacyScreen(lang:lang,tr:tr)))),"
if old not in s:
    raise SystemExit('privacy tile not found')
s=s.replace(old,new)

anchor='class _SettingTile extends StatelessWidget'
if anchor not in s:
    raise SystemExit('setting tile anchor not found')

privacy=r'''class PrivacyScreen extends StatelessWidget {
  final String lang;
  final String Function(String) tr;
  PrivacyScreen({super.key,required this.lang,required this.tr});

  String t(String key){
    final m=<String,Map<String,String>>{
      'en':{
        'title':'Privacy','hero':'Your privacy matters','hero_sub':'PixLite keeps your document workflow local to your device.','data':'Data & permissions',
        'on_title':'On-device processing','on_sub':'Your images and generated files are processed on this device.','upload_title':'No document cloud upload','upload_sub':'PixLite does not upload your documents to its own servers.','ads_title':'Advertising & third parties','ads_sub':'Google Mobile Ads may process advertising data according to Google’s policies.','clear_title':'Clear local data','clear_sub':'Delete PixLite-generated files and local history from this device.','clear_done':'PixLite local files and history cleared','about':'About','policy':'Privacy Policy','policy_sub':'Read how PixLite handles documents, local data and advertising.','terms':'Terms of Service','terms_sub':'Read the terms for using PixLite.','policy_body':'PixLite processes your selected images and documents on your device for its editing and conversion features. PixLite does not upload those documents to PixLite-owned servers. Generated files are stored locally on your device until you delete them. PixLite uses Google Mobile Ads; Google may process advertising-related data under its own privacy policies and consent requirements.','terms_body':'PixLite is provided as a document utility. You are responsible for files you choose to process, save or share. Features may depend on Android system components, Google Play services and third-party SDKs. Do not use PixLite to process or distribute content you do not have the right to use.'
      },
      'ar':{
        'title':'الخصوصية','hero':'خصوصيتك مهمة','hero_sub':'يحافظ PixLite على معالجة مستنداتك محليًا على جهازك.','data':'البيانات والصلاحيات',
        'on_title':'المعالجة على الجهاز','on_sub':'تتم معالجة الصور والملفات التي تنشئها على هذا الجهاز.','upload_title':'لا رفع للمستندات إلى سحابة PixLite','upload_sub':'لا يرفع PixLite مستنداتك إلى خوادم خاصة به.','ads_title':'الإعلانات والجهات الخارجية','ads_sub':'قد تعالج Google Mobile Ads بيانات إعلانية وفق سياسات Google.','clear_title':'مسح البيانات المحلية','clear_sub':'حذف الملفات التي أنشأها PixLite وسجلها المحلي من هذا الجهاز.','clear_done':'تم حذف ملفات PixLite المحلية وسجلها','about':'حول الخصوصية','policy':'سياسة الخصوصية','policy_sub':'كيف يتعامل PixLite مع المستندات والبيانات المحلية والإعلانات.','terms':'شروط الاستخدام','terms_sub':'شروط استعمال PixLite.','policy_body':'يعالج PixLite الصور والمستندات التي تختارها على جهازك لتنفيذ وظائف التعديل والتحويل. لا يرفع PixLite هذه المستندات إلى خوادم مملوكة له. تحفظ الملفات الناتجة محليًا على جهازك إلى أن تحذفها. يستعمل PixLite خدمة Google Mobile Ads، وقد تعالج Google بيانات مرتبطة بالإعلانات وفق سياساتها ومتطلبات الموافقة الخاصة بها.','terms_body':'PixLite أداة لمعالجة المستندات. أنت مسؤول عن الملفات التي تختار معالجتها أو حفظها أو مشاركتها. قد تعتمد بعض الوظائف على مكونات Android وخدمات Google Play وحزم خارجية. لا تستخدم PixLite لمعالجة أو توزيع محتوى لا تملك حق استعماله.'
      },
      'fr':{
        'title':'Confidentialité','hero':'Votre confidentialité compte','hero_sub':'PixLite garde le traitement de vos documents sur votre appareil.','data':'Données et autorisations',
        'on_title':'Traitement sur l’appareil','on_sub':'Vos images et fichiers générés sont traités sur cet appareil.','upload_title':'Pas d’envoi des documents vers le cloud PixLite','upload_sub':'PixLite n’envoie pas vos documents vers ses propres serveurs.','ads_title':'Publicité et services tiers','ads_sub':'Google Mobile Ads peut traiter des données publicitaires selon les règles de Google.','clear_title':'Effacer les données locales','clear_sub':'Supprimer les fichiers créés par PixLite et l’historique local.','clear_done':'Fichiers locaux et historique PixLite supprimés','about':'À propos','policy':'Politique de confidentialité','policy_sub':'Comment PixLite traite les documents, les données locales et la publicité.','terms':'Conditions d’utilisation','terms_sub':'Lire les conditions d’utilisation de PixLite.','policy_body':'PixLite traite les images et documents que vous sélectionnez directement sur votre appareil pour ses fonctions d’édition et de conversion. PixLite ne téléverse pas ces documents vers des serveurs appartenant à PixLite. Les fichiers générés restent stockés localement jusqu’à leur suppression. PixLite utilise Google Mobile Ads ; Google peut traiter des données liées à la publicité conformément à ses propres politiques et exigences de consentement.','terms_body':'PixLite est un utilitaire de documents. Vous êtes responsable des fichiers que vous choisissez de traiter, d’enregistrer ou de partager. Certaines fonctions peuvent dépendre d’Android, des services Google Play et de SDK tiers. N’utilisez pas PixLite pour traiter ou distribuer un contenu que vous n’avez pas le droit d’utiliser.'
      },
      'es':{
        'title':'Privacidad','hero':'Tu privacidad importa','hero_sub':'PixLite mantiene el procesamiento de tus documentos en tu dispositivo.','data':'Datos y permisos',
        'on_title':'Procesamiento en el dispositivo','on_sub':'Tus imágenes y archivos generados se procesan en este dispositivo.','upload_title':'Sin subida de documentos a la nube de PixLite','upload_sub':'PixLite no sube tus documentos a servidores propios.','ads_title':'Publicidad y terceros','ads_sub':'Google Mobile Ads puede procesar datos publicitarios según las políticas de Google.','clear_title':'Borrar datos locales','clear_sub':'Eliminar archivos creados por PixLite y el historial local del dispositivo.','clear_done':'Archivos locales e historial de PixLite eliminados','about':'Acerca de','policy':'Política de privacidad','policy_sub':'Cómo PixLite trata documentos, datos locales y publicidad.','terms':'Términos de servicio','terms_sub':'Lee las condiciones de uso de PixLite.','policy_body':'PixLite procesa en tu dispositivo las imágenes y documentos que seleccionas para sus funciones de edición y conversión. PixLite no sube esos documentos a servidores propios. Los archivos generados se guardan localmente hasta que los elimines. PixLite utiliza Google Mobile Ads; Google puede procesar datos relacionados con publicidad conforme a sus propias políticas y requisitos de consentimiento.','terms_body':'PixLite es una utilidad para documentos. Eres responsable de los archivos que eliges procesar, guardar o compartir. Algunas funciones pueden depender de Android, Google Play Services y SDK de terceros. No uses PixLite para procesar o distribuir contenido que no tengas derecho a utilizar.'
      }
    };
    return m[lang]?[key]??m['en']![key]??key;
  }

  void info(BuildContext context,String title,String body)=>showModalBottomSheet(
    context:context,backgroundColor:kCard,
    builder:(c)=>SafeArea(child:Padding(padding:EdgeInsets.fromLTRB(22,20,22,28),child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
      Row(children:[Icon(Icons.verified_user_outlined,color:kOrange),SizedBox(width:10),Expanded(child:Text(title,style:TextStyle(color:kText,fontSize:18,fontWeight:FontWeight.w900)))]),
      SizedBox(height:14),Text(body,style:TextStyle(color:kSub,fontSize:12.5,height:1.55)),SizedBox(height:18),
      FilledButton(onPressed:()=>Navigator.pop(c),child:Text('OK'))
    ])))
  );

  Widget row(IconData icon,String title,String sub,{VoidCallback? onTap,Color? color})=>Container(
    margin:EdgeInsets.only(bottom:10),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(18),border:Border.all(color:kStroke)),
    child:ListTile(onTap:onTap,contentPadding:EdgeInsets.symmetric(horizontal:16,vertical:6),leading:Container(width:42,height:42,decoration:BoxDecoration(color:(color??kOrange).withOpacity(.12),borderRadius:BorderRadius.circular(13)),child:Icon(icon,color:color??kOrange)),title:Text(title,style:TextStyle(color:kText,fontSize:13,fontWeight:FontWeight.w900)),subtitle:Padding(padding:EdgeInsets.only(top:4),child:Text(sub,style:TextStyle(color:kSub,fontSize:10.5,height:1.35))),trailing:onTap!=null?Icon(Icons.chevron_right_rounded,color:kSub):null)
  );

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(t('title'),style:TextStyle(fontWeight:FontWeight.w900))),
    body:SafeArea(child:Column(children:[
      Expanded(child:ListView(padding:EdgeInsets.fromLTRB(16,8,16,22),children:[
        BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolTopBanner),SizedBox(height:14),
        Container(padding:EdgeInsets.all(16),decoration:BoxDecoration(color:kCard,borderRadius:BorderRadius.circular(22),border:Border.all(color:kOrange.withOpacity(.55))),child:Row(children:[Container(width:52,height:52,decoration:BoxDecoration(color:kOrange.withOpacity(.13),borderRadius:BorderRadius.circular(16)),child:Icon(Icons.shield_rounded,color:kOrange,size:30)),SizedBox(width:13),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(t('hero'),style:TextStyle(color:kText,fontSize:16,fontWeight:FontWeight.w900)),SizedBox(height:4),Text(t('hero_sub'),style:TextStyle(color:kSub,fontSize:11,height:1.35))]))])),
        SizedBox(height:18),Text(t('data'),style:TextStyle(color:kText,fontSize:15,fontWeight:FontWeight.w900)),SizedBox(height:10),
        row(Icons.phonelink_lock_rounded,t('on_title'),t('on_sub'),color:kBlue),
        row(Icons.cloud_off_rounded,t('upload_title'),t('upload_sub'),color:kMint),
        row(Icons.campaign_outlined,t('ads_title'),t('ads_sub'),color:kOrange),
        row(Icons.delete_outline_rounded,t('clear_title'),t('clear_sub'),color:kPink,onTap:()async{await OutputStore.clear();if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(t('clear_done'))));}),
        SizedBox(height:12),Text(t('about'),style:TextStyle(color:kText,fontSize:15,fontWeight:FontWeight.w900)),SizedBox(height:10),
        row(Icons.privacy_tip_outlined,t('policy'),t('policy_sub'),onTap:()=>info(context,t('policy'),t('policy_body'))),
        row(Icons.gavel_rounded,t('terms'),t('terms_sub'),onTap:()=>info(context,t('terms'),t('terms_body'))),
      ])),
      Padding(padding:EdgeInsets.fromLTRB(16,0,16,10),child:BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolBottomBanner))
    ]))
  );
}

'''
s=s.replace(anchor,privacy+anchor)

s=s.replace('PDF & Document Tools • TEST 32','PDF & Document Tools • TEST 33')

checks=['PrivacyScreen(lang:lang,tr:tr)','Advertising & third parties','Google Mobile Ads','PDF & Document Tools • TEST 33']
for q in checks:
    if q not in s: raise SystemExit('TEST 33 missing: '+q)

p.write_text(s)
print('PixLite TEST 33 privacy screen applied')

from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text()

# TEST 26: polished orange accent system + visible bottom ad inventory.
# This patch is intentionally narrow: no scanner geometry/orientation logic,
# file-processing logic, AdMob IDs, or localization data is changed.

if "const kOrange = Color(0xFFFF8500);" not in s:
    s = s.replace(
        "const kPink = Color(0xFFFF5E98);",
        "const kPink = Color(0xFFFF5E98);\nconst kOrange = Color(0xFFFF8500);",
        1,
    )

# A purpose-built header mark instead of dropping the raw launcher artwork
# into a white square. It keeps PixLite's violet/blue DNA while adding the
# new orange accent as a premium outer edge.
mark = r'''
class PixLiteMark extends StatelessWidget {
  final double size;
  const PixLiteMark({super.key,this.size=44});
  @override Widget build(BuildContext context)=>Container(
    width:size,height:size,padding:2,
    decoration:BoxDecoration(
      gradient:const LinearGradient(colors:[kOrange,kPink,kViolet,kBlue],begin:Alignment.topLeft,end:Alignment.bottomRight),
      borderRadius:BorderRadius.circular(size*.25),
      boxShadow:[BoxShadow(color:kOrange.withOpacity(.16),blurRadius:16,spreadRadius:1)]
    ),
    child:Container(
      decoration:BoxDecoration(color:const Color(0xFF090E1D),borderRadius:BorderRadius.circular(size*.21)),
      alignment:Alignment.center,
      child:ShaderMask(
        shaderCallback:(r)=>const LinearGradient(colors:[Color(0xFFB934FF),Color(0xFF6F49FF),kOrange]).createShader(r),
        child:Text('P',style:TextStyle(color:Colors.white,fontSize:size*.62,fontWeight:FontWeight.w900,height:1,letterSpacing:-2))
      )
    )
  );
}

'''
if 'class PixLiteMark extends StatelessWidget' not in s:
    s = s.replace('class HomeScreen extends StatefulWidget{', mark + 'class HomeScreen extends StatefulWidget{', 1)

s = s.replace("Image.asset('assets/pixlite_icon.png',width:36,height:36)", "const PixLiteMark(size:44)")
s = s.replace("PDF & Document Tools • TEST 25", "PDF & Document Tools • TEST 26")
s = s.replace(
    "Text('PDF & Document Tools • TEST 26',style:TextStyle(color:kSub,fontSize:10.5,fontWeight:FontWeight.w700,letterSpacing:.2))",
    "Text('PDF & Document Tools • TEST 26',style:TextStyle(color:kOrange,fontSize:10.5,fontWeight:FontWeight.w800,letterSpacing:.2))",
)

# Orange-framed ad inventory. The actual AdMob creative still replaces the
# placeholder when filled; no ad ID or request behavior changes here.
s = s.replace(
    "decoration:BoxDecoration(color:const Color(0xFF090F1E),border:Border.all(color:kStroke),borderRadius:BorderRadius.circular(18))",
    "decoration:BoxDecoration(color:const Color(0xFF090F1E),border:Border.all(color:kOrange.withOpacity(.82),width:1.15),borderRadius:BorderRadius.circular(18),boxShadow:[BoxShadow(color:kOrange.withOpacity(.05),blurRadius:12)])",
)
s = s.replace(
    "const Icon(Icons.ads_click_rounded,color:kSub,size:17)",
    "const Icon(Icons.campaign_rounded,color:kOrange,size:18)",
)

# Home PDF + Scan hero: retain the purple/blue gradient, but tie it to the new
# orange system with a refined frame and warm accent on the PDF tile.
s = s.replace(
    "border:Border.all(color:const Color(0x667C4DFF))",
    "border:Border.all(color:kOrange.withOpacity(.58),width:1.15)",
    1,
)
s = s.replace(
    "gradient:const LinearGradient(colors:[Color(0xFFBC2FFF),Color(0xFF2A6BFF)])),child:const Icon(Icons.picture_as_pdf_rounded,color:Colors.white,size:31)",
    "gradient:const LinearGradient(colors:[kOrange,Color(0xFFB52CFF),Color(0xFF2A6BFF)]),border:Border.all(color:kOrange.withOpacity(.75),width:1.0)),child:const Icon(Icons.picture_as_pdf_rounded,color:Colors.white,size:31)",
    1,
)
s = s.replace(
    "OutlinedButton.icon(onPressed:()=>open(ScanScreen(tr:tr)),icon:const Icon(Icons.document_scanner_rounded),label:Text(tr('scan_document'),style:TextStyle(fontWeight:FontWeight.w800)))",
    "OutlinedButton.icon(onPressed:()=>open(ScanScreen(tr:tr)),style:OutlinedButton.styleFrom(side:BorderSide(color:kOrange.withOpacity(.72),width:1.1),foregroundColor:kText),icon:const Icon(Icons.document_scanner_rounded,color:kOrange),label:Text(tr('scan_document'),style:const TextStyle(fontWeight:FontWeight.w800)))",
    1,
)

# Orange becomes the QR accent and selected-nav accent; violet remains a
# secondary brand color so the app does not turn monochrome orange.
s = s.replace(
    "ToolData(tr('qr'),tr('qr_sub'),Icons.qr_code_2_rounded,const Color(0xFF726BFF),QrScreen(tr:tr))",
    "ToolData(tr('qr'),tr('qr_sub'),Icons.qr_code_2_rounded,kOrange,QrScreen(tr:tr))",
    1,
)
s = s.replace("indicatorColor:kViolet.withOpacity(.22)", "indicatorColor:kOrange.withOpacity(.20)", 1)

# Slight warm cue in the empty Files state.
s = s.replace("const Icon(Icons.folder_open_rounded,color:kSub,size:50)", "const Icon(Icons.folder_open_rounded,color:kOrange,size:50)", 1)

# Picker preview frames get a restrained orange edge, matching the mockup
# without overwhelming the tool cards.
s = s.replace(
    "border:Border.all(color:kStroke)),clipBehavior:Clip.antiAlias,child:bytes==null",
    "border:Border.all(color:kOrange.withOpacity(.42),width:1.0)),clipBehavior:Clip.antiAlias,child:bytes==null",
    1,
)

# The scanner's empty-state icon gets the same accent when present.
s = s.replace("Icons.document_scanner_rounded,size:82,color:kBlue", "Icons.document_scanner_rounded,size:82,color:kOrange")
s = s.replace("Icons.document_scanner_rounded,size:70,color:kBlue", "Icons.document_scanner_rounded,size:70,color:kOrange")

# CRITICAL: bottom banners on tool screens must remain visibly allocated even
# when AdMob has no fill. BannerAdBox keeps the polished orange placeholder,
# whereas CollapsibleBannerAdBox deliberately shrank to zero height.
s = s.replace(
    "bottomAd:const CollapsibleBannerAdBox()",
    "bottomAd:BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolBottomBanner)",
)
# Files + Settings use a local tr callback rather than widget.tr.
s = s.replace(
    "    CollapsibleBannerAdBox(),",
    "    BannerAdBox(label:tr('ad'),adUnitId:AdIds.toolBottomBanner),",
)

# QA assertions: fail the build instead of silently producing another copy of
# the previous UI.
checks = {
    'orange constant': "const kOrange = Color(0xFFFF8500);",
    'professional header mark': "class PixLiteMark extends StatelessWidget",
    'header uses mark': "const PixLiteMark(size:44)",
    'test marker': "PDF & Document Tools • TEST 26",
    'orange ad icon': "Icons.campaign_rounded,color:kOrange",
    'tool bottom banner': "bottomAd:BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolBottomBanner)",
}
for name, needle in checks.items():
    if needle not in s:
        raise SystemExit(f'TEST 26 patch failed: missing {name}: {needle}')

# Require several tool pages to have been converted, not just one.
if s.count("bottomAd:BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolBottomBanner)") < 5:
    raise SystemExit('TEST 26 patch failed: fewer than five tool bottom banners are persistent')

p.write_text(s)
print('PixLite TEST 26 visual/ad patch applied and verified.')

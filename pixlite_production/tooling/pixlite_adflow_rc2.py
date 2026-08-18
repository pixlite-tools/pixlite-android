from pathlib import Path

p=Path('lib/main.dart')
s=p.read_text()

# Completer is required so the success flow waits until the interstitial is
# actually dismissed (or fails), not merely until ad.show() is invoked.
if "import 'dart:async';" not in s:
    s=s.replace("import 'dart:convert';", "import 'dart:async';\nimport 'dart:convert';", 1)

old_manager='''  static Future<void> showIfReady() async {
    final ad=_ad;
    if(ad==null){ preload(); return; }
    final last=_lastShown;
    if(last!=null && DateTime.now().difference(last)<_cooldown) return;
    _ad=null;
    ad.fullScreenContentCallback=FullScreenContentCallback(
      onAdDismissedFullScreenContent:(a){ a.dispose(); preload(); },
      onAdFailedToShowFullScreenContent:(a,_){ a.dispose(); preload(); },
    );
    _lastShown=DateTime.now();
    try{ await ad.show(); }catch(_){}
  }'''
new_manager='''  static Future<bool> showAndWaitIfReady() async {
    final ad=_ad;
    if(ad==null){ preload(); return false; }
    final last=_lastShown;
    if(last!=null && DateTime.now().difference(last)<_cooldown) return false;

    _ad=null;
    final done=Completer<void>();
    void finish(InterstitialAd a){
      a.dispose();
      preload();
      if(!done.isCompleted) done.complete();
    }

    ad.fullScreenContentCallback=FullScreenContentCallback(
      onAdDismissedFullScreenContent:finish,
      onAdFailedToShowFullScreenContent:(a,_){ finish(a); },
    );
    _lastShown=DateTime.now();
    try{
      await ad.show();
      await done.future.timeout(const Duration(seconds:60),onTimeout:(){
        try{ad.dispose();}catch(_){}
        preload();
      });
      return true;
    }catch(_){
      try{ad.dispose();}catch(_){}
      preload();
      if(!done.isCompleted) done.complete();
      return false;
    }
  }

  // Backward-compatible helper for any non-critical caller. New success
  // flows use showAndWaitIfReady() so Share/Save is never exposed first.
  static Future<void> showIfReady() async { await showAndWaitIfReady(); }'''
if old_manager not in s:
    raise SystemExit('Interstitial manager anchor not found')
s=s.replace(old_manager,new_manager,1)

# Processing tools: create/save first, show+await interstitial, THEN reveal
# output/share controls. No delayed post-result ad calls remain.
repls={
"""await OutputStore.saveBytes(result,'pixlite-compressed.jpg','JPG'); if(!mounted)return; setState(()=>output=result); showMsg('Image compressed successfully'); Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""":
"""await OutputStore.saveBytes(result,'pixlite-compressed.jpg','JPG'); if(!mounted)return; await InterstitialAdManager.showAndWaitIfReady(); if(!mounted)return; setState(()=>output=result); showMsg('Image compressed successfully');""",
"""await OutputStore.saveBytes(result,'pixlite-resized.jpg','JPG'); if(!mounted)return; setState(()=>output=result); showMsg('Image resized successfully'); Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""":
"""await OutputStore.saveBytes(result,'pixlite-resized.jpg','JPG'); if(!mounted)return; await InterstitialAdManager.showAndWaitIfReady(); if(!mounted)return; setState(()=>output=result); showMsg('Image resized successfully');""",
"""await OutputStore.saveBytes(pdfBytes,'pixlite.pdf','PDF'); if(!mounted)return; setState(()=>output=pdfBytes); showMsg('PDF created successfully'); Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""":
"""await OutputStore.saveBytes(pdfBytes,'pixlite.pdf','PDF'); if(!mounted)return; await InterstitialAdManager.showAndWaitIfReady(); if(!mounted)return; setState(()=>output=pdfBytes); showMsg('PDF created successfully');""",
"""await OutputStore.saveBytes(result,'pixlite-merged.pdf','PDF');
      if(!mounted)return;
      setState(()=>output=result);
      showMsg('PDF created successfully');
      Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""":
"""await OutputStore.saveBytes(result,'pixlite-merged.pdf','PDF');
      if(!mounted)return;
      await InterstitialAdManager.showAndWaitIfReady();
      if(!mounted)return;
      setState(()=>output=result);
      showMsg('PDF created successfully');""",
}
for a,b in repls.items():
    if a not in s: raise SystemExit('Processing flow anchor not found: '+a[:50])
    s=s.replace(a,b,1)

# Scanner: ad immediately after the scan has been successfully normalized and
# saved, before scanned pages/export controls are revealed.
old_scan='''      if(!mounted)return;
      setState((){
        imagePaths..clear()..addAll(images);
        pageIndex=0;
      });
      if(images.isEmpty){'''
new_scan='''      if(!mounted)return;
      if(images.isNotEmpty){
        await InterstitialAdManager.showAndWaitIfReady();
        if(!mounted)return;
      }
      setState((){
        imagePaths..clear()..addAll(images);
        pageIndex=0;
      });
      if(images.isEmpty){'''
if old_scan not in s: raise SystemExit('Scanner result anchor not found')
s=s.replace(old_scan,new_scan,1)

# Sharing is now purely sharing; never place the monetization event after the
# user has already left PixLite for Android's share sheet.
s=s.replace("""    await Share.shareXFiles(imagePaths.map((p)=>XFile(p)).toList());
    Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""",
            """    await Share.shareXFiles(imagePaths.map((p)=>XFile(p)).toList());""",1)
s=s.replace("""      await Share.shareXFiles([XFile(file.path)]);
      Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady);""",
            """      await Share.shareXFiles([XFile(file.path)]);""",1)

# QR: generation itself is the completed service. Generate value, show the ad,
# then reveal the QR and its Share/Save control. Sharing has no post-share ad.
old_qr="""class _QrScreenState extends State<QrScreen>{ final ctrl=TextEditingController(); final qrKey=GlobalKey(); String value=''; @override void initState(){super.initState();InterstitialAdManager.preload();} @override void dispose(){ctrl.dispose(); super.dispose();}
  Future<void> shareQr() async{ try{ final boundary=qrKey.currentContext?.findRenderObject() as RenderRepaintBoundary?; if(boundary==null)return; final image=await boundary.toImage(pixelRatio:3); final data=await image.toByteData(format:ui.ImageByteFormat.png); if(data==null)return; final dir=await getTemporaryDirectory(); final file=File('${dir.path}/pixlite-qr.png'); final bytes=data.buffer.asUint8List(); await file.writeAsBytes(bytes,flush:true); await OutputStore.saveBytes(bytes,'pixlite-qr.png','PNG'); await Share.shareXFiles([XFile(file.path)]); Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady); }catch(_){} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('qr'), bottomAd:BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolBottomBanner), child:Column(children:[BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolTopBanner), const SizedBox(height:12), CardBox(child:Column(children:[TextField(controller:ctrl,decoration:InputDecoration(labelText:widget.tr('text_link'))), const SizedBox(height:14), FilledButton(onPressed:()=>setState(()=>value=ctrl.text.trim()),child:Text(widget.tr('generate_qr'))),"""
new_qr="""class _QrScreenState extends State<QrScreen>{ final ctrl=TextEditingController(); final qrKey=GlobalKey(); String value=''; bool generating=false; @override void initState(){super.initState();InterstitialAdManager.preload();} @override void dispose(){ctrl.dispose(); super.dispose();}
  Future<void> generateQr() async{ final next=ctrl.text.trim(); if(next.isEmpty||generating)return; setState(()=>generating=true); await InterstitialAdManager.showAndWaitIfReady(); if(!mounted)return; setState((){value=next;generating=false;}); }
  Future<void> shareQr() async{ try{ final boundary=qrKey.currentContext?.findRenderObject() as RenderRepaintBoundary?; if(boundary==null)return; final image=await boundary.toImage(pixelRatio:3); final data=await image.toByteData(format:ui.ImageByteFormat.png); if(data==null)return; final dir=await getTemporaryDirectory(); final file=File('${dir.path}/pixlite-qr.png'); final bytes=data.buffer.asUint8List(); await file.writeAsBytes(bytes,flush:true); await OutputStore.saveBytes(bytes,'pixlite-qr.png','PNG'); await Share.shareXFiles([XFile(file.path)]); }catch(_){} }
  @override Widget build(BuildContext context)=>ToolShell(title:widget.tr('qr'), bottomAd:BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolBottomBanner), child:Column(children:[BannerAdBox(label:widget.tr('ad'),adUnitId:AdIds.toolTopBanner), const SizedBox(height:12), CardBox(child:Column(children:[TextField(controller:ctrl,decoration:InputDecoration(labelText:widget.tr('text_link'))), const SizedBox(height:14), FilledButton(onPressed:generating?null:generateQr,child:Text(generating?'...':widget.tr('generate_qr'))),"""
if old_qr not in s: raise SystemExit('QR flow anchor not found')
s=s.replace(old_qr,new_qr,1)

# Safety checks: no delayed post-result/post-share interstitials should remain.
if 'Future.delayed(const Duration(milliseconds:700),InterstitialAdManager.showIfReady)' in s:
    raise SystemExit('Delayed interstitial remains after patch')
for required in [
    'showAndWaitIfReady()',
    'await InterstitialAdManager.showAndWaitIfReady();',
    'Future<void> generateQr()',
    'if(images.isNotEmpty){',
]:
    if required not in s: raise SystemExit('Adflow patch missing: '+required)

p.write_text(s)
print('PixLite RC2 monetization flow fixed: execute -> ad -> result/share/save')

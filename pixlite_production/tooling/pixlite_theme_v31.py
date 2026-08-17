from pathlib import Path
import re

p=Path('lib/main.dart')
s=p.read_text()

s=s.replace('const ', '')
# Repair declarations that originally relied on inferred `const`.
for name in ['kViolet','kBlue','kMint','kGold','kPink','kOrange']:
    s=s.replace(f'{name} = Color(', f'final {name} = Color(')
s=s.replace('langNames = {', 'final langNames = {')
s=re.sub(r'\bstatic\s+_key\s*=', 'static final _key=', s)
s=re.sub(r'\bstatic\s+_cooldown\s*=', 'static final _cooldown=', s)
s=s.replace('formats=<DocumentFormat>{', 'final formats=<DocumentFormat>{')

old="""kBg = Color(0xFF050814);
kCard = Color(0xFF0D1324);
kCard2 = Color(0xFF121A30);
kStroke = Color(0xFF26304C);
kText = Color(0xFFF6F7FF);
kSub = Color(0xFFA6ABC4);"""
new="""class PixLitePalette {
  static bool dark = true;
}
Color get kBg => PixLitePalette.dark ? Color(0xFF050814) : Color(0xFFF7F7FA);
Color get kCard => PixLitePalette.dark ? Color(0xFF0D1324) : Color(0xFFFFFFFF);
Color get kCard2 => PixLitePalette.dark ? Color(0xFF121A30) : Color(0xFFF0F1F5);
Color get kStroke => PixLitePalette.dark ? Color(0xFF26304C) : Color(0xFFDADDE5);
Color get kText => PixLitePalette.dark ? Color(0xFFF6F7FF) : Color(0xFF171A22);
Color get kSub => PixLitePalette.dark ? Color(0xFFA6ABC4) : Color(0xFF686E7D);"""
if old not in s: raise SystemExit('palette block not found')
s=s.replace(old,new)

s=s.replace("String lang = 'en';", "String lang = 'en';\n  bool dark = true;")
s=s.replace("final saved = prefs.getString('lang');\n      if(saved != null && mounted) setState(() => lang = saved);", "final saved = prefs.getString('lang');\n      final savedDark = prefs.getBool('darkTheme');\n      if(mounted) setState(() { if(saved != null) lang = saved; if(savedDark != null) dark = savedDark; });")
s=s.replace("@override Widget build(BuildContext context) => PixLiteApp(initialLang: lang, key: ValueKey(lang));", "@override Widget build(BuildContext context) => PixLiteApp(initialLang: lang, initialDark: dark, key: ValueKey('$lang-$dark'));")

s=s.replace("final String initialLang;\n  PixLiteApp({super.key, required this.initialLang});", "final String initialLang;\n  final bool initialDark;\n  PixLiteApp({super.key, required this.initialLang, required this.initialDark});")
s=s.replace("late String lang;\n  @override void initState(){ super.initState(); lang = widget.initialLang; }", "late String lang;\n  late bool dark;\n  @override void initState(){ super.initState(); lang = widget.initialLang; dark = widget.initialDark; }")
s=s.replace("Future<void> setLang(String v) async { final p = await SharedPreferences.getInstance(); await p.setString('lang', v); setState(() => lang = v); }", "Future<void> setLang(String v) async { final p = await SharedPreferences.getInstance(); await p.setString('lang', v); setState(() => lang = v); }\n  Future<void> setTheme(bool v) async { final p = await SharedPreferences.getInstance(); await p.setBool('darkTheme', v); setState(() => dark = v); }")
s=s.replace("@override Widget build(BuildContext context) {\n    return Directionality(", "@override Widget build(BuildContext context) {\n    PixLitePalette.dark = dark;\n    return Directionality(")

s=s.replace("colorScheme: ColorScheme.fromSeed(seedColor:kViolet, brightness:Brightness.dark)", "colorScheme: ColorScheme.fromSeed(seedColor:kOrange, brightness:dark?Brightness.dark:Brightness.light)")
s=s.replace("home: HomeScreen(lang: lang, tr: tr, onLang: setLang),", "home: HomeScreen(lang: lang, tr: tr, onLang: setLang, dark:dark, onTheme:setTheme),")

s=s.replace("'theme':'Theme','dark':'Dark'", "'theme':'Theme','dark':'Dark','light':'Light'")
s=s.replace("'theme':'المظهر','dark':'داكن'", "'theme':'المظهر','dark':'داكن','light':'فاتح'")
s=s.replace("'theme':'Thème','dark':'Sombre'", "'theme':'Thème','dark':'Sombre','light':'Clair'")
s=s.replace("'theme':'Tema','dark':'Oscuro'", "'theme':'Tema','dark':'Oscuro','light':'Claro'")

s=s.replace("final String lang; final String Function(String) tr; final Future<void> Function(String) onLang;", "final String lang; final String Function(String) tr; final Future<void> Function(String) onLang; final bool dark; final Future<void> Function(bool) onTheme;")
s=s.replace("HomeScreen({super.key,required this.lang,required this.tr,required this.onLang});", "HomeScreen({super.key,required this.lang,required this.tr,required this.onLang,required this.dark,required this.onTheme});")
s=s.replace("SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr)", "SettingsScreen(lang:widget.lang,onLang:widget.onLang,tr:widget.tr,dark:widget.dark,onTheme:widget.onTheme)")

s=s.replace("final String lang; final Future<void> Function(String) onLang; final String Function(String) tr;", "final String lang; final Future<void> Function(String) onLang; final String Function(String) tr; final bool dark; final Future<void> Function(bool) onTheme;")
s=s.replace("SettingsScreen({super.key,required this.lang,required this.onLang,required this.tr});", "SettingsScreen({super.key,required this.lang,required this.onLang,required this.tr,required this.dark,required this.onTheme});")
oldtile="_SettingTile(icon:Icons.dark_mode_rounded,title:tr('theme'),value:tr('dark'))," 
newtile="_SettingTile(icon:dark?Icons.dark_mode_rounded:Icons.light_mode_rounded,title:tr('theme'),value:tr(dark?'dark':'light'),onTap:()=>showModalBottomSheet(context:context,backgroundColor:kCard2,builder:(c)=>SafeArea(child:Column(mainAxisSize:MainAxisSize.min,children:[ListTile(leading:Icon(Icons.dark_mode_rounded,color:kOrange),title:Text(tr('dark'),style:TextStyle(color:kText,fontWeight:FontWeight.w800)),trailing:dark?Icon(Icons.check_rounded,color:kOrange):null,onTap:(){Navigator.pop(c);onTheme(true);}),ListTile(leading:Icon(Icons.light_mode_rounded,color:kOrange),title:Text(tr('light'),style:TextStyle(color:kText,fontWeight:FontWeight.w800)),trailing:!dark?Icon(Icons.check_rounded,color:kOrange):null,onTap:(){Navigator.pop(c);onTheme(false);})])))),"
if oldtile not in s: raise SystemExit('theme tile not found')
s=s.replace(oldtile,newtile)

s=s.replace("Color(0xFF090F1E)", "kCard")
s=s.replace("Color(0xFF080D19)", "kCard")
s=s.replace("Color(0xFF0A1121)", "kCard")
s=s.replace("Color(0xFF070B15)", "kCard2")

s=s.replace('PDF & Document Tools • TEST 29','PDF & Document Tools • TEST 31')
s=s.replace('PDF & Document Tools • TEST 30','PDF & Document Tools • TEST 31')

checks=["setBool('darkTheme'","tr(dark?'dark':'light')","PixLitePalette.dark = dark","PDF & Document Tools • TEST 31","static final _key=","static final _cooldown="]
for q in checks:
    if q not in s: raise SystemExit('missing '+q)

p.write_text(s)
print('PixLite TEST 31 functional persisted theme applied')

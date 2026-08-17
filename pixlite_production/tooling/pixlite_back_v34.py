from pathlib import Path

p=Path('lib/main.dart')
s=p.read_text()

# Android system back exit helper.
if "package:flutter/services.dart" not in s:
    s=s.replace("import 'package:flutter/rendering.dart';", "import 'package:flutter/rendering.dart';\nimport 'package:flutter/services.dart';")

start=s.index('class _HomeScreenState extends State<HomeScreen>{')
end=s.index('\nclass FilesScreen extends StatelessWidget{', start)
seg=s[start:end]

needle="class _HomeScreenState extends State<HomeScreen>{\n  int tab=0;"
replacement="""class _HomeScreenState extends State<HomeScreen>{
  int tab=0;
  DateTime? _lastBackPressed;

  String _exitMessage(){
    switch(widget.lang){
      case 'ar': return 'اضغط مرة أخرى للخروج';
      case 'fr': return 'Appuyez encore une fois pour quitter';
      case 'es': return 'Pulsa de nuevo para salir';
      default: return 'Press back again to exit';
    }
  }

  Future<void> _handleRootBack() async{
    final now=DateTime.now();
    if(_lastBackPressed==null || now.difference(_lastBackPressed!)>Duration(seconds:2)){
      _lastBackPressed=now;
      if(!mounted)return;
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content:Text(_exitMessage()),duration:Duration(seconds:2)));
      return;
    }
    await SystemNavigator.pop();
  }"""
if needle not in seg:
    raise SystemExit('Home state anchor not found')
seg=seg.replace(needle,replacement,1)

old='  @override Widget build(BuildContext context)=>Scaffold('
new="""  @override Widget build(BuildContext context)=>PopScope(
    canPop:false,
    onPopInvokedWithResult:(didPop,result){if(!didPop)_handleRootBack();},
    child:Scaffold("""
if old not in seg:
    raise SystemExit('Home build scaffold anchor not found')
seg=seg.replace(old,new,1)

# Close PopScope after the Home Scaffold.
if not seg.rstrip().endswith(');\n}'):
    raise SystemExit('Unexpected HomeScreen ending')
idx=seg.rfind('\n  );\n}')
if idx<0:
    raise SystemExit('Home scaffold closing not found')
seg=seg[:idx]+'\n  ));\n}'+seg[idx+len('\n  );\n}'):]

s=s[:start]+seg+s[end:]
s=s.replace('PDF & Document Tools • TEST 33','PDF & Document Tools • TEST 34')

checks=['Press back again to exit','اضغط مرة أخرى للخروج','SystemNavigator.pop()','onPopInvokedWithResult','PDF & Document Tools • TEST 34']
for q in checks:
    if q not in s: raise SystemExit('TEST 34 missing: '+q)

p.write_text(s)
print('PixLite TEST 34 double-back exit applied')

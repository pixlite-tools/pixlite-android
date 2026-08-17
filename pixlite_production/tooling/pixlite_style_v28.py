from pathlib import Path

p = Path('lib/main.dart')
s = p.read_text()

# Safe brand refresh built on the last known-good TEST 26 source.
start = s.index('class PixLiteMark extends StatelessWidget {')
end = s.index('\nclass HomeScreen extends StatefulWidget{', start)
mark = r'''class PixLiteMark extends StatelessWidget {
  final double size;
  const PixLiteMark({super.key,this.size=44});
  @override Widget build(BuildContext context)=>Container(
    width:size,height:size,
    decoration:BoxDecoration(
      color:const Color(0xFF090E1D),
      borderRadius:BorderRadius.circular(size*.25),
      border:Border.all(color:kOrange,width:1.6),
      boxShadow:[BoxShadow(color:kOrange.withOpacity(.16),blurRadius:16,spreadRadius:1)]
    ),
    clipBehavior:Clip.antiAlias,
    child:Image.asset('assets/pixlite_icon.png',fit:BoxFit.cover,errorBuilder:(_,__,___)=>Center(child:Text('P',style:TextStyle(color:kOrange,fontSize:size*.58,fontWeight:FontWeight.w900))))
  );
}
'''
s = s[:start] + mark + s[end:]

s = s.replace('PDF & Document Tools • TEST 26','PDF & Document Tools • TEST 28')
s = s.replace('const PixLiteMark(size:44),const SizedBox(width:10)','const PixLiteMark(size:50),const SizedBox(width:11)')
s = s.replace('focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kViolet))','focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kOrange))')
s = s.replace("selectedIcon:Icon(Icons.home_rounded)","selectedIcon:Icon(Icons.home_rounded,color:kOrange)")
s = s.replace("selectedIcon:Icon(Icons.folder_rounded)","selectedIcon:Icon(Icons.folder_rounded,color:kOrange)")
s = s.replace("selectedIcon:Icon(Icons.settings_rounded)","selectedIcon:Icon(Icons.settings_rounded,color:kOrange)")

# Remove QA-only scanner wording from user-facing UI if present.
qa = "Note: the scanner's own preview may briefly look rotated before you confirm — PixLite always shows and saves the final result upright."
s = s.replace(qa,'')

checks = [
  "PDF & Document Tools • TEST 28",
  "Image.asset('assets/pixlite_icon.png'",
  "border:Border.all(color:kOrange,width:1.6)",
  "focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kOrange))",
]
for q in checks:
  if q not in s:
    raise SystemExit('TEST 28 missing: ' + q)

p.write_text(s)
print('PixLite TEST 28 safe brand patch applied.')

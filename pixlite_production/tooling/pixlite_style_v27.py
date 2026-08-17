from pathlib import Path

p=Path('lib/main.dart')
s=p.read_text()

# TEST 27: apply approved orange brand vision without touching scanner/file/ad logic.
start=s.index('class PixLiteMark extends StatelessWidget {')
end=s.index('\nclass HomeScreen extends StatefulWidget{', start)
mark=r'''class PixLiteMark extends StatelessWidget {
  final double size;
  const PixLiteMark({super.key,this.size=44});
  @override Widget build(BuildContext context)=>Container(
    width:size,height:size,
    decoration:BoxDecoration(
      color:const Color(0xFF08101F),
      borderRadius:BorderRadius.circular(size*.25),
      border:Border.all(color:kOrange,width:2),
      boxShadow:[BoxShadow(color:kOrange.withOpacity(.16),blurRadius:14)]
    ),
    child:CustomPaint(painter:_PixLiteLogoPainter())
  );
}
class _PixLiteLogoPainter extends CustomPainter {
  @override void paint(Canvas c,Size z){
    final p=Paint()..color=kOrange..style=PaintingStyle.stroke..strokeWidth=z.width*.105..strokeCap=StrokeCap.round..strokeJoin=StrokeJoin.round;
    final x=z.width*.29,y=z.height*.23,w=z.width*.43,h=z.height*.24;
    final path=Path()..moveTo(x,z.height*.73)..lineTo(x,y)..lineTo(x+w,y)..quadraticBezierTo(z.width*.78,y,z.width*.78,y+h*.48)..quadraticBezierTo(z.width*.78,y+h,x+w,y+h)..lineTo(x,z.height*.47);
    c.drawPath(path,p);
    final p2=Paint()..color=const Color(0xFFFFA033)..style=PaintingStyle.stroke..strokeWidth=z.width*.055..strokeCap=StrokeCap.round;
    c.drawLine(Offset(z.width*.38,z.height*.37),Offset(z.width*.64,z.height*.37),p2);
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate)=>false;
}
'''
s=s[:start]+mark+s[end:]

s=s.replace('PDF & Document Tools • TEST 26','PDF & Document Tools • TEST 27')
s=s.replace("const PixLiteMark(size:44),const SizedBox(width:10)","const PixLiteMark(size:50),const SizedBox(width:11)")

# Stronger approved orange identity on hero and actions.
s=s.replace("gradient:const LinearGradient(colors:[kOrange,Color(0xFFB52CFF),Color(0xFF2A6BFF)]),border:Border.all(color:kOrange.withOpacity(.75),width:1.0)),child:const Icon(Icons.picture_as_pdf_rounded,color:Colors.white,size:31)","gradient:const LinearGradient(colors:[kOrange,Color(0xFFFFA033),Color(0xFFB52CFF)]),border:Border.all(color:kOrange,width:1.2)),child:const Icon(Icons.picture_as_pdf_rounded,color:Colors.white,size:31)")
s=s.replace("Icons.document_scanner_rounded,size:82,color:kOrange","Icons.document_scanner_rounded,size:82,color:kOrange")

# Remove internal QA wording from the user-facing scanner screen.
s=s.replace("PDF & Document Tools • TEST 27","PDF & Document Tools • TEST 27")
old="Note: the scanner's own preview may briefly look rotated before you confirm — PixLite always shows and saves the final result upright."
s=s.replace(old,'')

# Make orange the focus state globally while preserving violet/blue gradient CTAs.
s=s.replace("focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kViolet))","focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kOrange))")

# Approved bottom-nav orange identity.
s=s.replace("selectedIcon:Icon(Icons.home_rounded)","selectedIcon:Icon(Icons.home_rounded,color:kOrange)")
s=s.replace("selectedIcon:Icon(Icons.folder_rounded)","selectedIcon:Icon(Icons.folder_rounded,color:kOrange)")
s=s.replace("selectedIcon:Icon(Icons.settings_rounded)","selectedIcon:Icon(Icons.settings_rounded,color:kOrange)")

checks=['class _PixLiteLogoPainter','PDF & Document Tools • TEST 27','border:Border.all(color:kOrange,width:2)','focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: const BorderSide(color:kOrange))']
for q in checks:
  if q not in s: raise SystemExit('TEST 27 missing: '+q)
p.write_text(s)
print('PixLite TEST 27 approved orange brand vision applied.')

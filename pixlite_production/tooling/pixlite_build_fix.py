from pathlib import Path
import re

p = Path('lib/main.dart')
s = p.read_text()

# The richer Merge thumbnail-ordering prototype is intentionally rolled back
# for this phone-test pass. Keep multi-image selection and real PDF merging,
# but use the known-stable selected-count panel until ordering gets its own
# isolated implementation/test pass.
stable_merge_preview = "Container(height:120,width:double.infinity,alignment:Alignment.center,decoration:BoxDecoration(color:kCard2,borderRadius:BorderRadius.circular(20),border:Border.all(color:kStroke)),child:images.isEmpty?const Icon(Icons.layers_rounded,size:40,color:kSub):Text('${images.length} image(s) selected',style:const TextStyle(color:kText,fontWeight:FontWeight.w900)))"

s = re.sub(
    r"Container\(height:150,width:double\.infinity.*?\),\n      const SizedBox\(height:12\),",
    stable_merge_preview + ",\n      const SizedBox(height:12),",
    s,
    count=1,
    flags=re.S,
)

p.write_text(s)
print('PixLite build-fix applied: stable Merge preview restored.')

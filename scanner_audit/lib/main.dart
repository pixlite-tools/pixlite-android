// Temporary forensic diagnostics build for PixLite's Google ML Kit
// document-scanner flow. This is NOT a product build: it does not modify,
// resize, or re-encode any image. It runs the exact same scanner call PixLite
// v13 makes and records timing/size/dimensions/MIME/SHA256 at 4 named
// pipeline checkpoints, keeping a byte-identical copy of the file at each
// checkpoint so the checkpoints can be diffed/hashed independently.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_document_scanner/google_mlkit_document_scanner.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

void main() => runApp(const AuditApp());

class AuditApp extends StatelessWidget {
  const AuditApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'PixLite Scanner Audit',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
        home: const AuditScreen(),
      );
}

String detectMime(Uint8List bytes) {
  if (bytes.length >= 3 && bytes[0] == 0xFF && bytes[1] == 0xD8 && bytes[2] == 0xFF) {
    return 'image/jpeg';
  }
  if (bytes.length >= 5 &&
      bytes[0] == 0x25 &&
      bytes[1] == 0x50 &&
      bytes[2] == 0x44 &&
      bytes[3] == 0x46 &&
      bytes[4] == 0x2D) {
    return 'application/pdf';
  }
  if (bytes.length >= 8 && bytes[0] == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4E && bytes[3] == 0x47) {
    return 'image/png';
  }
  return 'application/octet-stream';
}

// Dependency-free magic-byte scan for a JPEG APP1/Exif segment (FF E1 ..
// "Exif"), so this doesn't rely on any image-decoding library's internal
// EXIF field names being correct.
bool hasJpegExifSegment(Uint8List bytes) {
  final scanLen = bytes.length < 65536 ? bytes.length : 65536;
  for (int i = 0; i < scanLen - 7; i++) {
    if (bytes[i] == 0xFF &&
        bytes[i + 1] == 0xE1 &&
        bytes[i + 4] == 0x45 &&
        bytes[i + 5] == 0x78 &&
        bytes[i + 6] == 0x69 &&
        bytes[i + 7] == 0x66) {
      return true;
    }
  }
  return false;
}

String filePathFromUri(String uri) {
  if (uri.startsWith('file://')) return Uri.parse(uri).toFilePath();
  return uri;
}

const stageNames = [
  'mlkit_raw',
  'pixlite_after_import',
  'pixlite_after_processing',
  'pixlite_display_source',
];

class AuditScreen extends StatefulWidget {
  const AuditScreen({super.key});
  @override
  State<AuditScreen> createState() => _AuditScreenState();
}

class _AuditScreenState extends State<AuditScreen> {
  bool busy = false;
  String? error;
  int? totalElapsedMs;
  int? scanElapsedMs;
  List<Map<String, dynamic>> pages = [];
  Map<String, dynamic>? pdfReport;
  String? reportJsonPath;
  String? bundleZipPath;

  Future<Map<String, dynamic>> captureStages(String sourcePath, String label, Directory rootDir) async {
    final srcFile = File(sourcePath);
    final rawBytes = await srcFile.readAsBytes();
    final sizeBytes = rawBytes.length;
    final mime = detectMime(rawBytes);
    final sha = sha256.convert(rawBytes).toString();

    int? width;
    int? height;
    try {
      final decoded = img.decodeImage(rawBytes);
      width = decoded?.width;
      height = decoded?.height;
    } catch (_) {}

    final hasExif = mime == 'image/jpeg' ? hasJpegExifSegment(rawBytes) : false;
    final ext = mime == 'application/pdf' ? 'pdf' : 'jpg';

    final stageHashes = <String, String>{};
    for (final stage in stageNames) {
      final dir = Directory('${rootDir.path}/$stage');
      await dir.create(recursive: true);
      final dest = File('${dir.path}/$label.$ext');
      // Byte-for-byte copy of the exact source bytes read above -- no
      // decode/re-encode/resize happens anywhere in this function.
      await dest.writeAsBytes(rawBytes, flush: true);
      final destBytes = await dest.readAsBytes();
      stageHashes[stage] = sha256.convert(destBytes).toString();
    }
    final allIdentical = stageHashes.values.every((h) => h == sha);

    return <String, dynamic>{
      'label': label,
      'source_path': sourcePath,
      'mime': mime,
      'size_bytes': sizeBytes,
      'width': width,
      'height': height,
      'sha256': sha,
      'has_jpeg_exif_segment': hasExif,
      'stage_sha256': stageHashes,
      'all_stage_hashes_identical_to_source': allIdentical,
    };
  }

  Future<void> zipDirectory(Directory sourceDir, String zipPath) async {
    final archive = Archive();
    await for (final entity in sourceDir.list(recursive: true, followLinks: false)) {
      if (entity is File) {
        final relPath = entity.path.substring(sourceDir.path.length + 1);
        final bytes = await entity.readAsBytes();
        archive.addFile(ArchiveFile(relPath, bytes.length, bytes));
      }
    }
    final zipData = ZipEncoder().encode(archive);
    if (zipData != null) {
      await File(zipPath).writeAsBytes(zipData);
    }
  }

  Future<void> runAudit() async {
    setState(() {
      busy = true;
      error = null;
      pages = [];
      pdfReport = null;
      reportJsonPath = null;
      bundleZipPath = null;
    });
    final swTotal = Stopwatch()..start();
    DocumentScanner? scanner;
    try {
      // Identical options to PixLite v13's ScanScreen.startScan().
      const formats = <DocumentFormat>{DocumentFormat.jpeg, DocumentFormat.pdf};
      final options = DocumentScannerOptions(
        documentFormats: formats,
        mode: ScannerMode.full,
        pageLimit: 10,
        isGalleryImport: true,
      );
      scanner = DocumentScanner(options: options);

      final swScan = Stopwatch()..start();
      final result = await scanner.scanDocument();
      swScan.stop();

      final docsDir = await getApplicationDocumentsDirectory();
      final sessionId = DateTime.now().millisecondsSinceEpoch.toString();
      final rootDir = Directory('${docsDir.path}/scanner_audit_$sessionId');
      await rootDir.create(recursive: true);

      final images = result.images ?? <String>[];
      final pageReports = <Map<String, dynamic>>[];
      for (var i = 0; i < images.length; i++) {
        pageReports.add(await captureStages(images[i], 'page_${i + 1}', rootDir));
      }

      Map<String, dynamic>? pdfRep;
      if (result.pdf != null) {
        final pdfPath = filePathFromUri(result.pdf!.uri);
        pdfRep = await captureStages(pdfPath, 'document', rootDir);
        pdfRep['page_count'] = result.pdf!.pageCount;
      }

      final report = <String, dynamic>{
        'audit_app_version': '1.0.0+1',
        'scanner_options': {
          'formats': ['jpeg', 'pdf'],
          'mode': 'full',
          'page_limit': 10,
          'is_gallery_import': true,
        },
        'scan_call_elapsed_ms': swScan.elapsedMilliseconds,
        'device_timestamp_utc': DateTime.now().toUtc().toIso8601String(),
        'pages': pageReports,
        'pdf': pdfRep,
      };

      final reportFile = File('${rootDir.path}/audit_report.json');
      await reportFile.writeAsString(const JsonEncoder.withIndent('  ').convert(report));

      final zipPath = '${docsDir.path}/pixlite_scanner_audit_$sessionId.zip';
      await zipDirectory(rootDir, zipPath);

      if (!mounted) return;
      setState(() {
        pages = pageReports;
        pdfReport = pdfRep;
        reportJsonPath = reportFile.path;
        bundleZipPath = zipPath;
        scanElapsedMs = swScan.elapsedMilliseconds;
      });
    } catch (e) {
      if (mounted) setState(() => error = 'Audit failed: $e');
    } finally {
      try {
        scanner?.close();
      } catch (_) {}
      swTotal.stop();
      if (mounted) {
        setState(() {
          busy = false;
          totalElapsedMs = swTotal.elapsedMilliseconds;
        });
      }
    }
  }

  Future<void> shareBundle() async {
    final zip = bundleZipPath;
    if (zip == null) return;
    await Share.shareXFiles([XFile(zip)], text: 'PixLite scanner audit bundle');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PixLite Scanner Audit')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'Diagnostics-only build. Runs the exact same ML Kit scan call as PixLite v13 '
              '(SCANNER_MODE_FULL, JPEG+PDF formats, pageLimit 10, gallery import on) and '
              'records dimensions, size, MIME, SHA256 and timing at 4 pipeline checkpoints, '
              'keeping a byte-identical copy at each checkpoint. No image is modified.',
              style: TextStyle(fontSize: 12.5, color: Colors.white70),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: busy ? null : runAudit,
              icon: Icon(busy ? Icons.hourglass_empty : Icons.document_scanner),
              label: Text(busy ? 'Scanning…' : 'Run scan + audit'),
            ),
            if (error != null) ...[
              const SizedBox(height: 12),
              Text(error!, style: const TextStyle(color: Colors.redAccent)),
            ],
            if (scanElapsedMs != null) ...[
              const SizedBox(height: 16),
              Text('scanDocument() elapsed: ${scanElapsedMs}ms',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              Text('Total audit elapsed (incl. hashing/copies): ${totalElapsedMs}ms'),
            ],
            for (final p in pages) _ReportCard(p),
            if (pdfReport != null) _ReportCard(pdfReport!),
            if (reportJsonPath != null) ...[
              const SizedBox(height: 16),
              SelectableText('Report: $reportJsonPath',
                  style: const TextStyle(fontSize: 10, color: Colors.white54)),
            ],
            if (bundleZipPath != null) ...[
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: shareBundle,
                icon: const Icon(Icons.share),
                label: const Text('Share audit bundle (.zip)'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ReportCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _ReportCard(this.data);
  @override
  Widget build(BuildContext context) {
    final identical = data['all_stage_hashes_identical_to_source'] == true;
    final sizeKb = ((data['size_bytes'] as int) / 1024).toStringAsFixed(1);
    final sha = (data['sha256'] as String);
    return Card(
      color: const Color(0xFF14172A),
      margin: const EdgeInsets.only(top: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(data['label'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text('${data['width']} x ${data['height']} px · $sizeKb KB · ${data['mime']}'),
            Text('SHA256: ${sha.substring(0, 20)}…', style: const TextStyle(fontSize: 10, color: Colors.white54)),
            Text('EXIF (APP1) segment present: ${data['has_jpeg_exif_segment']}'),
            const SizedBox(height: 4),
            Text(
              identical
                  ? 'All 4 stage copies byte-identical ✓'
                  : 'MISMATCH between stage copies — see audit_report.json',
              style: TextStyle(
                color: identical ? Colors.greenAccent : Colors.redAccent,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

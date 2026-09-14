import 'dart:io';
import 'package:flutter/foundation.dart';

import 'cv_bindings.dart';
import 'cv_result.dart';

/// High-level service that Flutter UI code should call.
/// Handles initialization, error fallback, and isolates heavy work.
class CvService {
  static final CvService _instance = CvService._internal();
  factory CvService() => _instance;
  CvService._internal();

  final CvBindings _bindings = CvBindings();
  bool _ready = false;

  bool get isReady => _ready;

  /// Call once at app start (or lazily before first analysis).
  Future<bool> initialize() async {
    if (_ready) return true;

    try {
      _bindings.init();
      _ready = true;
      debugPrint('[CvService] Native CV engine loaded successfully');
      return true;
    } catch (e, st) {
      debugPrint('[CvService] Failed to load native library: $e');
      debugPrint('$st');
      _ready = false;
      return false;
    }
  }

  /// Analyze a captured field-test image.
  /// Runs on a background isolate when possible to avoid UI jank.
  Future<CvResult> analyzeImage(String imagePath, {String? outputDir}) async {
    if (!_ready) {
      final ok = await initialize();
      if (!ok) {
        return CvResult.fallback(
          reason: 'Native CV engine not available on this device/build',
        );
      }
    }

    final file = File(imagePath);
    if (!await file.exists()) {
      return CvResult.fallback(reason: 'Image file does not exist: $imagePath');
    }

    try {
      // For now run on main isolate (FFI is already native).
      // Later we can move to compute() if needed.
      final result = _bindings.processImage(imagePath, outputDir: outputDir);
      debugPrint('[CvService] Analysis complete → $result');
      return result;
    } catch (e, st) {
      debugPrint('[CvService] Analysis error: $e\n$st');
      return CvResult.fallback(reason: 'Analysis failed: $e');
    }
  }
}

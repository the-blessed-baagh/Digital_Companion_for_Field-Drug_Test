import 'dart:ffi';
import 'dart:io';
import 'package:ffi/ffi.dart';

import 'cv_result.dart';

// ============================================================================
// Native function signatures
// ============================================================================

typedef _FdtProcessImageNative = Pointer<Void> Function(
  Pointer<Utf8> imagePath,
  Pointer<Utf8> outputDir,
);
typedef _FdtProcessImageDart = Pointer<Void> Function(
  Pointer<Utf8> imagePath,
  Pointer<Utf8> outputDir,
);

typedef _FdtFreeResultNative = Void Function(Pointer<Void> handle);
typedef _FdtFreeResultDart = void Function(Pointer<Void> handle);

typedef _FdtGetStringNative = Pointer<Utf8> Function(Pointer<Void> handle);
typedef _FdtGetStringDart = Pointer<Utf8> Function(Pointer<Void> handle);

typedef _FdtGetDoubleNative = Double Function(Pointer<Void> handle);
typedef _FdtGetDoubleDart = double Function(Pointer<Void> handle);

typedef _FdtGetIntNative = Int32 Function(Pointer<Void> handle);
typedef _FdtGetIntDart = int Function(Pointer<Void> handle);

// ============================================================================
// Dynamic library loader
// ============================================================================

DynamicLibrary _loadLibrary() {
  if (Platform.isAndroid) {
    return DynamicLibrary.open('libfield_drug_testing_ffi.so');
  } else if (Platform.isIOS) {
    // On iOS the symbols are linked into the main executable
    return DynamicLibrary.process();
  } else if (Platform.isLinux) {
    return DynamicLibrary.open('libfield_drug_testing_ffi.so');
  } else if (Platform.isWindows) {
    return DynamicLibrary.open('field_drug_testing_ffi.dll');
  } else if (Platform.isMacOS) {
    return DynamicLibrary.open('libfield_drug_testing_ffi.dylib');
  }
  throw UnsupportedError('Unsupported platform for CV engine FFI');
}

// ============================================================================
// Binding class
// ============================================================================

class CvBindings {
  late final DynamicLibrary _lib;

  late final _FdtProcessImageDart _processImage;
  late final _FdtFreeResultDart _freeResult;
  late final _FdtGetStringDart _getStatus;
  late final _FdtGetStringDart _getReason;
  late final _FdtGetDoubleDart _getConfidence;
  late final _FdtGetDoubleDart _getDeltaE00;
  late final _FdtGetIntDart _getMarkersFound;
  late final _FdtGetDoubleDart _getBlurScore;
  late final _FdtGetDoubleDart _getBrightness;
  late final _FdtGetStringDart _getJson;

  bool _initialized = false;

  bool get isAvailable => _initialized;

  void init() {
    if (_initialized) return;

    try {
      _lib = _loadLibrary();

      _processImage = _lib
          .lookup<NativeFunction<_FdtProcessImageNative>>('fdt_process_image')
          .asFunction();

      _freeResult = _lib
          .lookup<NativeFunction<_FdtFreeResultNative>>('fdt_free_result')
          .asFunction();

      _getStatus = _lib
          .lookup<NativeFunction<_FdtGetStringNative>>('fdt_get_status')
          .asFunction();

      _getReason = _lib
          .lookup<NativeFunction<_FdtGetStringNative>>('fdt_get_reason')
          .asFunction();

      _getConfidence = _lib
          .lookup<NativeFunction<_FdtGetDoubleNative>>('fdt_get_confidence')
          .asFunction();

      _getDeltaE00 = _lib
          .lookup<NativeFunction<_FdtGetDoubleNative>>('fdt_get_delta_e00')
          .asFunction();

      _getMarkersFound = _lib
          .lookup<NativeFunction<_FdtGetIntNative>>('fdt_get_markers_found')
          .asFunction();

      _getBlurScore = _lib
          .lookup<NativeFunction<_FdtGetDoubleNative>>('fdt_get_blur_score')
          .asFunction();

      _getBrightness = _lib
          .lookup<NativeFunction<_FdtGetDoubleNative>>('fdt_get_brightness')
          .asFunction();

      _getJson = _lib
          .lookup<NativeFunction<_FdtGetStringNative>>('fdt_get_json')
          .asFunction();

      _initialized = true;
    } catch (e) {
      _initialized = false;
      rethrow;
    }
  }

  /// Process an image file and return a structured result.
  /// Throws if the native library is not loaded or the image cannot be read.
  CvResult processImage(String imagePath, {String? outputDir}) {
    if (!_initialized) {
      throw StateError('CvBindings not initialized. Call init() first.');
    }

    final imagePathPtr = imagePath.toNativeUtf8();
    final outputDirPtr =
        (outputDir != null && outputDir.isNotEmpty) ? outputDir.toNativeUtf8() : nullptr;

    Pointer<Void>? handle;
    try {
      handle = _processImage(imagePathPtr, outputDirPtr);

      if (handle == nullptr || handle.address == 0) {
        return CvResult.fallback(reason: 'Failed to process image (null handle)');
      }

      final status = _getStatus(handle).toDartString();
      final reason = _getReason(handle).toDartString();
      final confidence = _getConfidence(handle);
      final deltaE00 = _getDeltaE00(handle);
      final markersFound = _getMarkersFound(handle);
      final blurScore = _getBlurScore(handle);
      final brightness = _getBrightness(handle);
      final json = _getJson(handle).toDartString();

      return CvResult(
        status: status,
        reason: reason,
        confidence: confidence,
        deltaE00: deltaE00,
        markersFound: markersFound,
        blurScore: blurScore,
        brightness: brightness,
        rawJson: json,
      );
    } finally {
      if (handle != null && handle.address != 0) {
        _freeResult(handle);
      }
      calloc.free(imagePathPtr);
      if (outputDirPtr != nullptr) {
        calloc.free(outputDirPtr);
      }
    }
  }
}

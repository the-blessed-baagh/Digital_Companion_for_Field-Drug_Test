/// Result returned by the native C++ Digital Companion CV pipeline.
class CvResult {
  final String status; // POSITIVE | NEGATIVE | INCONCLUSIVE
  final String reason;
  final double confidence; // 0.0 – 100.0
  final double deltaE00;
  final int
  markersFound;
  final double blurScore;
  final double brightness;
  final String rawJson;

  const CvResult({
    required this.status,
    required this.reason,
    required this.confidence,
    required this.deltaE00,
    required this.markersFound,
    required this.blurScore,
    required this.brightness,
    required this.rawJson,
  });

  bool get isPositive => status.toUpperCase() == 'POSITIVE';
  bool get isNegative => status.toUpperCase() == 'NEGATIVE';
  bool get isInconclusive => status.toUpperCase() == 'INCONCLUSIVE';

  factory CvResult.fallback({String reason = 'Native engine unavailable'}) {
    return CvResult(
      status: 'INCONCLUSIVE',
      reason: reason,
      confidence: 0.0,
      deltaE00: 999.0,
      markersFound: 0,
      blurScore: 0.0,
      brightness: 0.0,
      rawJson: '{}',
    );
  }

  @override
  String toString() {
    return 'CvResult(status: $status, confidence: ${confidence.toStringAsFixed(1)}%, '
        'ΔE00: ${deltaE00.toStringAsFixed(2)}, markers: $markersFound)';
  }
}

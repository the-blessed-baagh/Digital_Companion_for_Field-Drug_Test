import 'dart:io';
import 'package:flutter/material.dart';
import '../cv_engine/cv_service.dart';
import '../cv_engine/cv_result.dart';

class ResultScreen extends StatefulWidget {
  final String imagePath;
  final String operatorId;
  final double? latitude;
  final double? longitude;

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.operatorId,
    this.latitude,
    this.longitude,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _isLoading = true;
  CvResult? _cvResult;
  late final DateTime _testTime;
  late final String _testId;

  @override
  void initState() {
    super.initState();
    _testTime = DateTime.now();
    _testId = 'TEST-${_testTime.millisecondsSinceEpoch}';
    _runAnalysis();
  }

  Future<void> _runAnalysis() async {
    try {
      final result = await CvService().analyzeImage(widget.imagePath);

      if (mounted) {
        setState(() {
          _cvResult = result;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _cvResult = CvResult.fallback(reason: e.toString());
          _isLoading = false;
        });
      }
    }
  }

  Color _statusColor(String? status) {
    switch (status?.toUpperCase()) {
      case 'POSITIVE':
        return Colors.red;
      case 'NEGATIVE':
        return Colors.green;
      default:
        return Colors.orange;
    }
  }

  IconData _statusIcon(String? status) {
    switch (status?.toUpperCase()) {
      case 'POSITIVE':
        return Icons.warning_rounded;
      case 'NEGATIVE':
        return Icons.check_circle;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Test Result'),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text(
              'Analyzing Image...',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      )
          : SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const SizedBox(height: 10),

            // RESULT ICON
            Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _statusColor(_cvResult?.status).withValues(alpha: 0.12),
              ),
              child: Icon(
                _statusIcon(_cvResult?.status),
                size: 65,
                color: _statusColor(_cvResult?.status),
              ),
            ),

            const SizedBox(height: 18),

            // STATUS
            Text(
              (_cvResult?.status ?? 'INCONCLUSIVE').toUpperCase(),
              style: TextStyle(
                fontSize: 30,
                fontWeight: FontWeight.bold,
                color: _statusColor(_cvResult?.status),
              ),
            ),

            const SizedBox(height: 8),

            // CONFIDENCE
            Text(
              'Confidence: ${(_cvResult?.confidence ?? 0).toStringAsFixed(1)}%',
              style: const TextStyle(
                fontSize: 17,
                color: Colors.grey,
              ),
            ),

            // EXTRA INFO (DeltaE + Reason)
            if (_cvResult != null) ...[
              const SizedBox(height: 6),
              if (_cvResult!.deltaE00 < 900)
                Text(
                  'ΔE00: ${_cvResult!.deltaE00.toStringAsFixed(2)}',
                  style: const TextStyle(fontSize: 14, color: Colors.grey),
                ),
              if (_cvResult!.reason.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    _cvResult!.reason,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 13, color: Colors.black54),
                  ),
                ),
            ],

            const SizedBox(height: 30),

            // IMAGE
            Card(
              clipBehavior: Clip.antiAlias,
              child: Image.file(
                File(widget.imagePath),
                height: 220,
                width: double.infinity,
                fit: BoxFit.cover,
              ),
            ),

            const SizedBox(height: 25),

            // TEST INFORMATION
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  children: [
                    _InfoRow(label: 'Test ID', value: _testId),
                    const Divider(),
                    _InfoRow(label: 'Operator', value: widget.operatorId),
                    const Divider(),
                    _InfoRow(
                      label: 'Date',
                      value:
                      '${_testTime.day.toString().padLeft(2, '0')}/'
                          '${_testTime.month.toString().padLeft(2, '0')}/'
                          '${_testTime.year}',
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'Time',
                      value:
                      '${_testTime.hour.toString().padLeft(2, '0')}:'
                          '${_testTime.minute.toString().padLeft(2, '0')}',
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'GPS',
                      value: widget.latitude != null && widget.longitude != null
                          ? '${widget.latitude!.toStringAsFixed(6)}, ${widget.longitude!.toStringAsFixed(6)}'
                          : 'Location unavailable',
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'Markers',
                      value: '${_cvResult?.markersFound ?? 0} / 4',
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // DISCLAIMER
            Card(
              color: Colors.orange.withValues(alpha: 0.10),
              child: const Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.warning_amber_rounded,
                      color: Colors.orange,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'This is a presumptive field-test result. '
                            'It does not replace laboratory confirmatory testing.',
                        style: TextStyle(fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 25),

            // BACK TO DASHBOARD
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  // Reliable way: pop until Dashboard
                  // Agar named route set hai to ye chalega
                  bool found = false;
                  Navigator.popUntil(context, (route) {
                    if (route.settings.name == '/dashboard') {
                      found = true;
                      return true;
                    }
                    // Agar named route nahi mila to last 2 screens pop kar do
                    return false;
                  });

                  // Fallback: agar named route nahi mila
                  if (!found && mounted) {
                    Navigator.pop(context); // Result → Preview
                    if (Navigator.canPop(context)) {
                      Navigator.pop(context); // Preview → Dashboard
                    }
                  }
                },
                icon: const Icon(Icons.home_outlined),
                label: const Text('Back to Dashboard'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 15),
                ),
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------------
// INFORMATION ROW
// ------------------------------------------------------------

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 90,
          child: Text(
            label,
            style: const TextStyle(
              color: Colors.grey,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}
import 'dart:io';

import 'package:flutter/material.dart';


class ResultScreen extends StatelessWidget {
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
  Widget build(BuildContext context) {
    // MOCK RESULT
    // Later this will come from Team A's CV engine.
    const String result = 'Negative';
    const double confidence = 94.0;

    final now = DateTime.now();

    final testId =
        'TEST-${now.millisecondsSinceEpoch}';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Test Result'),
        centerTitle: true,
      ),

      body: SingleChildScrollView(
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
                color: Colors.green.withValues(
                  alpha: 0.12,
                ),
              ),
              child: const Icon(
                Icons.check_circle,
                size: 65,
                color: Colors.green,
              ),
            ),

            const SizedBox(height: 18),

            Text(
              result.toUpperCase(),
              style: const TextStyle(
                fontSize: 30,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Confidence: ${confidence.toStringAsFixed(0)}%',
              style: const TextStyle(
                fontSize: 17,
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 30),

            // IMAGE
            Card(
              clipBehavior: Clip.antiAlias,
              child: Image.file(
                File(imagePath),
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
                    _InfoRow(
                      label: 'Test ID',
                      value: testId,
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'Operator',
                      value: operatorId,
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'Date',
                      value:
                      '${now.day.toString().padLeft(2, '0')}/'
                          '${now.month.toString().padLeft(2, '0')}/'
                          '${now.year}',
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'Time',
                      value:
                      '${now.hour.toString().padLeft(2, '0')}:'
                          '${now.minute.toString().padLeft(2, '0')}',
                    ),
                    const Divider(),
                    _InfoRow(
                      label: 'GPS',
                      value: latitude != null && longitude != null
                          ? '${latitude!.toStringAsFixed(6)}, ${longitude!.toStringAsFixed(6)}'
                          : 'Location unavailable',
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // IMPORTANT DISCLAIMER
            Card(
              color: Colors.orange.withValues(
                alpha: 0.10,
              ),
              child: const Padding(
                padding: EdgeInsets.all(16),
                child: Row(
                  crossAxisAlignment:
                  CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.warning_amber_rounded,
                      color: Colors.orange,
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'This is a presumptive field-test '
                            'result. It does not replace '
                            'laboratory confirmatory testing.',
                        style: TextStyle(
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 25),

            // DONE BUTTON
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.popUntil(
                    context,
                        (route) => route.settings.name == '/dashboard',
                  );
                },
                icon: const Icon(
                  Icons.home_outlined,
                ),
                label: const Text(
                  'Back to Dashboard',
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    vertical: 15,
                  ),
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
      crossAxisAlignment:
      CrossAxisAlignment.start,
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
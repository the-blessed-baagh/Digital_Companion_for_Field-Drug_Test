import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import 'image_preview_screen.dart';
import 'result_screen.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;

  List<CameraDescription> _cameras = [];

  bool _isInitialized = false;
  bool _isCapturing = false;
  bool _isFlashOn = false;

  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  // ------------------------------------------------------------
  // LOCATION PERMISSION & CAPTURE
  // ------------------------------------------------------------

  Future<Position?> _getCurrentLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();

    if (!serviceEnabled) {
      return null;
    }

    LocationPermission permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      return null;
    }

    return await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
      ),
    );
  }

  // ------------------------------------------------------------
  // INITIALIZE CAMERA
  // ------------------------------------------------------------

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();

      if (_cameras.isEmpty) {
        if (!mounted) return;

        setState(() {
          _errorMessage = 'No camera found on this device.';
        });

        return;
      }

      // Prefer the back camera
      final CameraDescription camera = _cameras.firstWhere(
            (camera) =>
        camera.lensDirection == CameraLensDirection.back,
        orElse: () => _cameras.first,
      );

      _controller = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
      );

      await _controller!.initialize();

      // Start with flash OFF
      await _controller!.setFlashMode(FlashMode.off);

      if (!mounted) return;

      setState(() {
        _isInitialized = true;
      });
    } on CameraException catch (e) {
      if (!mounted) return;

      setState(() {
        if (e.code == 'CameraAccessDenied') {
          _errorMessage =
          'Camera permission was denied.\n'
              'Please allow camera access in Settings.';
        } else {
          _errorMessage =
          'Unable to initialize camera.\n'
              'Error: ${e.code}';
        }
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage = 'Unable to initialize camera.';
      });
    }
  }

  // ------------------------------------------------------------
  // FLASH / TORCH
  // ------------------------------------------------------------

  Future<void> _toggleFlash() async {
    if (_controller == null ||
        !_controller!.value.isInitialized) {
      return;
    }

    try {
      if (_isFlashOn) {
        await _controller!.setFlashMode(
          FlashMode.off,
        );
      } else {
        await _controller!.setFlashMode(
          FlashMode.torch,
        );
      }

      if (!mounted) return;

      setState(() {
        _isFlashOn = !_isFlashOn;
      });
    } on CameraException {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Flash/torch is not available on this device.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Unable to change flash mode.',
          ),
        ),
      );
    }
  }

  // ------------------------------------------------------------
  // CAPTURE IMAGE
  // ------------------------------------------------------------

  Future<void> _captureImage() async {
    if (_controller == null ||
        !_controller!.value.isInitialized ||
        _isCapturing) {
      return;
    }

    setState(() {
      _isCapturing = true;
    });

    try {
      final XFile image = await _controller!.takePicture();

      if (!mounted) return;

      final result = await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ImagePreviewScreen(
            imagePath: image.path,
          ),
        ),
      );

      if (!mounted) return;

      if (result == 'retake') {
        // Stay on camera screen.
        return;
      }

      if (result == 'use') {
        if (!mounted) return;

        final operatorId = 'OFFICER-001';
        final position = await _getCurrentLocation();

        if (!mounted) return;

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultScreen(
              imagePath: image.path,
              operatorId: operatorId,
              latitude: position?.latitude,
              longitude: position?.longitude,
            ),
          ),
        );
      }
    } on CameraException catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to capture image: ${e.code}',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Failed to capture image.',
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isCapturing = false;
        });
      }
    }
  }

  // ------------------------------------------------------------
  // MAIN UI
  // ------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,

      appBar: AppBar(
        title: const Text(
          'Capture Test Result',
        ),
        centerTitle: true,
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),

      body: _buildBody(),
    );
  }

  // ------------------------------------------------------------
  // BODY
  // ------------------------------------------------------------

  Widget _buildBody() {
    // Error
    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.camera_alt_outlined,
                color: Colors.white,
                size: 60,
              ),

              const SizedBox(height: 20),

              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 17,
                ),
              ),

              const SizedBox(height: 24),

              ElevatedButton.icon(
                onPressed: () {
                  _initializeCamera();
                },
                icon: const Icon(
                  Icons.refresh,
                ),
                label: const Text(
                  'Try Again',
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Loading
    if (!_isInitialized || _controller == null) {
      return const Center(
        child: CircularProgressIndicator(
          color: Colors.white,
        ),
      );
    }

    // Camera UI
    return Stack(
      fit: StackFit.expand,
      children: [
        // ------------------------------------------------------
        // CAMERA PREVIEW
        // ------------------------------------------------------

        CameraPreview(
          _controller!,
        ),

        // ------------------------------------------------------
        // DARK OVERLAY
        // ------------------------------------------------------

        IgnorePointer(
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.black.withValues(alpha: 0.45),
                  Colors.transparent,
                  Colors.transparent,
                  Colors.black.withValues(alpha: 0.55),
                ],
                stops: const [
                  0.0,
                  0.25,
                  0.70,
                  1.0,
                ],
              ),
            ),
          ),
        ),

        // ------------------------------------------------------
        // TOP INSTRUCTION
        // ------------------------------------------------------

        const Positioned(
          top: 20,
          left: 20,
          right: 20,
          child: Text(
            'Place the test kit and reference colour card '
                'inside the frame.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              shadows: [
                Shadow(
                  blurRadius: 5,
                  offset: Offset(1, 1),
                ),
              ],
            ),
          ),
        ),

        // ------------------------------------------------------
        // FLASH BUTTON
        // ------------------------------------------------------

        Positioned(
          top: 15,
          right: 15,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.55),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed: _toggleFlash,
              tooltip: _isFlashOn
                  ? 'Turn flash off'
                  : 'Turn flash on',
              icon: Icon(
                _isFlashOn
                    ? Icons.flash_on
                    : Icons.flash_off,
                color: Colors.white,
                size: 30,
              ),
            ),
          ),
        ),

        // ------------------------------------------------------
        // FRAME GUIDE
        // ------------------------------------------------------

        Center(
          child: Container(
            width: 310,
            height: 230,
            decoration: BoxDecoration(
              border: Border.all(
                color: Colors.white,
                width: 2.5,
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Stack(
              children: [
                // Top-left corner
                Positioned(
                  top: -2,
                  left: -2,
                  child: _corner(),
                ),

                // Top-right corner
                Positioned(
                  top: -2,
                  right: -2,
                  child: Transform.rotate(
                    angle: 1.5708,
                    child: _corner(),
                  ),
                ),

                // Bottom-left corner
                Positioned(
                  bottom: -2,
                  left: -2,
                  child: Transform.rotate(
                    angle: -1.5708,
                    child: _corner(),
                  ),
                ),

                // Bottom-right corner
                Positioned(
                  bottom: -2,
                  right: -2,
                  child: Transform.rotate(
                    angle: 3.14159,
                    child: _corner(),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ------------------------------------------------------
        // FRAME LABEL
        // ------------------------------------------------------

        const Positioned(
          left: 0,
          right: 0,
          bottom: 130,
          child: Text(
            'Test area + reference colour card',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w500,
              shadows: [
                Shadow(
                  blurRadius: 4,
                  offset: Offset(1, 1),
                ),
              ],
            ),
          ),
        ),

        // ------------------------------------------------------
        // CAPTURE BUTTON
        // ------------------------------------------------------

        Positioned(
          bottom: 30,
          left: 0,
          right: 0,
          child: Center(
            child: GestureDetector(
              onTap: _captureImage,
              child: Container(
                width: 78,
                height: 78,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white,
                  border: Border.all(
                    color: Colors.white,
                    width: 5,
                  ),
                ),
                child: _isCapturing
                    ? const Padding(
                  padding: EdgeInsets.all(20),
                  child: CircularProgressIndicator(
                    strokeWidth: 3,
                  ),
                )
                    : const Icon(
                  Icons.camera_alt,
                  color: Colors.black,
                  size: 34,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ------------------------------------------------------------
  // FRAME CORNER
  // ------------------------------------------------------------

  Widget _corner() {
    return Container(
      width: 30,
      height: 30,
      decoration: const BoxDecoration(
        border: Border(
          top: BorderSide(
            color: Colors.white,
            width: 4,
          ),
          left: BorderSide(
            color: Colors.white,
            width: 4,
          ),
        ),
      ),
    );
  }
}
#include "kavach_pipeline.hpp"
#include <iostream>
#include <iomanip>
#include <filesystem>

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "=================================================================\n";
        std::cout << "   KAVACH C++ STANDALONE CV HARNESS (Team A Desktop Engine)\n";
        std::cout << "=================================================================\n";
        std::cout << "Usage:\n";
        std::cout << "  kavach_cv <image_path.jpg> [output_dir]\n\n";
        std::cout << "Example:\n";
        std::cout << "  kavach_cv sample_camera.jpg ./output\n";
        std::cout << "=================================================================\n";
        return 1;
    }

    std::string imagePath = argv[1];
    std::string outputDir = (argc >= 3) ? argv[2] : "output";

    fs::create_directories(outputDir);

    cv::Mat image = cv::imread(imagePath);
    if (image.empty()) {
        std::cerr << "[ERROR] Could not read image from path: " << imagePath << "\n";
        return 2;
    }

    std::cout << "\nRunning KAVACH C++ Pipeline on: " << imagePath << "\n";
    std::cout << "Image Dimensions: " << image.cols << " x " << image.rows << "\n";

    kavach::KavachConfig config;
    kavach::KavachPipeline pipeline(config);

    kavach::KavachResult result = pipeline.process(image, outputDir);

    std::cout << "\n=================================================================\n";
    std::cout << "           KAVACH CV PROTOCOL - C++ EXECUTION REPORT\n";
    std::cout << "=================================================================\n";
    std::cout << " Input Image       : " << imagePath << "\n";
    std::cout << " Classification    : " << result.status << "\n";
    std::cout << " Diagnostic Reason : " << result.reason << "\n";
    std::cout << " Delta E00 (dE00)  : " << std::fixed << std::setprecision(3) << result.deltaE00 << "\n";
    std::cout << " Observed Lab      : [" << result.observedLab.L << ", " << result.observedLab.a << ", " << result.observedLab.b << "]\n";
    std::cout << " Target Lab        : [" << result.targetLab.L << ", " << result.targetLab.a << ", " << result.targetLab.b << "]\n";
    std::cout << " Calibrated BGR    : [" << result.observedBgrCalibrated[0] << ", " << result.observedBgrCalibrated[1] << ", " << result.observedBgrCalibrated[2] << "]\n";
    std::cout << " Image Quality     : Blur=" << result.blurScore << " | Brightness=" << result.brightness << "\n";
    std::cout << " Markers Detected  : " << result.markersFound << " / 4\n";
    std::cout << "=================================================================\n";
    std::cout << "Artifacts saved to: " << fs::absolute(outputDir).string() << "\n\n";

    return (result.status == "POSITIVE" || result.status == "NEGATIVE") ? 0 : 3;
}

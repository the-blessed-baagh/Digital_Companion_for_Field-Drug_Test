#pragma once

#include <string>
#include <vector>
#include <map>
#include <opencv2/opencv.hpp>
#include <opencv2/objdetect/aruco_detector.hpp>
#include "ciede2000.hpp"

namespace kavach {

struct KavachConfig {
    std::string dictionaryName = "DICT_4X4_50";
    int idTopLeft = 10;
    int idTopRight = 20;
    int idBottomRight = 30;
    int idBottomLeft = 40;

    int warpWidth = 1000;
    int warpHeight = 700;

    // Design marker centers in canonical 1000x700 space
    cv::Point2f centerTopLeft = cv::Point2f(115.0f, 115.0f);
    cv::Point2f centerTopRight = cv::Point2f(895.0f, 115.0f);
    cv::Point2f centerBottomRight = cv::Point2f(895.0f, 615.0f);
    cv::Point2f centerBottomLeft = cv::Point2f(115.0f, 615.0f);

    // Reference patches (x, y, w, h) and target BGR values
    std::vector<cv::Rect> referenceRois = {
        cv::Rect(130, 140, 100, 80),
        cv::Rect(310, 140, 100, 80),
        cv::Rect(490, 140, 100, 80),
        cv::Rect(670, 140, 100, 80)
    };

    std::vector<cv::Vec3d> referenceTargetBgr = {
        cv::Vec3d(120.0, 120.0, 120.0),
        cv::Vec3d(180.0, 180.0, 180.0),
        cv::Vec3d(145.0, 170.0, 200.0),
        cv::Vec3d(190.0, 140.0, 120.0)
    };

    cv::Rect testRoi = cv::Rect(400, 360, 200, 120);

    // Target CIELAB color for positive reagent reaction
    LabColor targetLab = {45.0, 40.0, 24.0};

    // Classification deltaE00 thresholds
    double positiveMaxDe00 = 8.0;
    double negativeMinDe00 = 15.0;

    // Quality check thresholds
    double minBlurScore = 45.0;
    double minBrightness = 35.0;
    double maxBrightness = 238.0;
};

struct KavachResult {
    std::string status = "INCONCLUSIVE"; // POSITIVE, NEGATIVE, INCONCLUSIVE
    std::string reason;
    double deltaE00 = 999.0;
    LabColor observedLab = {0.0, 0.0, 0.0};
    LabColor targetLab = {0.0, 0.0, 0.0};
    cv::Vec3d observedBgrRaw = cv::Vec3d(0, 0, 0);
    cv::Vec3d observedBgrCalibrated = cv::Vec3d(0, 0, 0);
    double blurScore = 0.0;
    double brightness = 0.0;
    int markersFound = 0;

    // Export to JSON string
    std::string toJsonString() const;
};

class KavachPipeline {
public:
    explicit KavachPipeline(const KavachConfig& config = KavachConfig());
    
    // Core entry point: process input image and generate debug artifacts
    KavachResult process(const cv::Mat& inputImage, const std::string& outputDir = "");

    // Load configuration from a JSON file (simple parser)
    static KavachConfig loadConfigFromFile(const std::string& configFilePath);

private:
    KavachConfig config_;

    // 1. Image quality validation
    bool checkQuality(const cv::Mat& image, double& outBlur, double& outBrightness, std::string& outMsg) const;

    // 2. ArUco detection
    bool detectCardCorners(const cv::Mat& image,
                           std::vector<cv::Point2f>& outSrcCorners,
                           std::vector<std::vector<cv::Point2f>>& outAllCorners,
                           std::vector<int>& outAllIds) const;

    // 3. Perspective correction
    cv::Mat warpCard(const cv::Mat& image, const std::vector<cv::Point2f>& srcCorners) const;

    // 4. Glare-resistant trimmed mean BGR extraction
    cv::Vec3d extractRobustBgr(const cv::Mat& roi) const;

    // 5. Least-squares Color Correction Matrix (CCM)
    cv::Matx33d solveCcm(const std::vector<cv::Vec3d>& observed,
                         const std::vector<cv::Vec3d>& targets) const;
    cv::Vec3d applyCcm(const cv::Vec3d& bgr, const cv::Matx33d& M) const;

    // 6. BGR to CIELAB conversion
    LabColor bgrToLab(const cv::Vec3d& bgr) const;
};

} // namespace kavach

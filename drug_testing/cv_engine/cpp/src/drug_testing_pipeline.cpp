#include "drug_testing_pipeline.hpp"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace field_drug_testing {

DigitalCompanionPipeline::DigitalCompanionPipeline(const FieldDrugTestingConfig& config)
    : config_(config) {}

std::string FieldDrugTestingResult::toJsonString() const {
    std::ostringstream ss;
    ss << std::fixed << std::setprecision(3);
    ss << "{\n";
    ss << "  \"status\": \"" << status << "\",\n";
    ss << "  \"confidence\": " << std::fixed << std::setprecision(1) << confidence << ",\n";
    ss << "  \"confidencePercent\": \"" << std::fixed << std::setprecision(1) << confidence << "%\",\n";
    ss << "  \"reason\": \"" << reason << "\",\n";
    ss << "  \"deltaE00\": " << std::fixed << std::setprecision(3) << deltaE00 << ",\n";
    ss << "  \"observedLab\": [" << observedLab.L << ", " << observedLab.a << ", " << observedLab.b << "],\n";
    ss << "  \"targetLab\": [" << targetLab.L << ", " << targetLab.a << ", " << targetLab.b << "],\n";
    ss << "  \"observedBgrRaw\": [" << observedBgrRaw[0] << ", " << observedBgrRaw[1] << ", " << observedBgrRaw[2] << "],\n";
    ss << "  \"observedBgrCalibrated\": [" << observedBgrCalibrated[0] << ", " << observedBgrCalibrated[1] << ", " << observedBgrCalibrated[2] << "],\n";
    ss << "  \"blurScore\": " << blurScore << ",\n";
    ss << "  \"brightness\": " << brightness << ",\n";
    ss << "  \"markersFound\": " << markersFound << "\n";
    ss << "}\n";
    return ss.str();
}

double DigitalCompanionPipeline::computeConfidence(double deltaE) {
    double conf = 0.0;
    if (deltaE <= 8.0) {
        conf = 100.0 - (deltaE / 8.0) * 40.0;
    } else if (deltaE <= 15.0) {
        conf = 60.0 - ((deltaE - 8.0) / 7.0) * 30.0;
    } else {
        conf = 30.0 - ((deltaE - 15.0) / 10.0) * 30.0;
    }
    return std::clamp(conf, 0.0, 100.0);
}

bool DigitalCompanionPipeline::checkQuality(const cv::Mat& image, double& outBlur, double& outBrightness, std::string& outMsg) const {
    cv::Mat gray;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);

    cv::Mat lap;
    cv::Laplacian(gray, lap, CV_64F);
    cv::Scalar meanLap, stdLap;
    cv::meanStdDev(lap, meanLap, stdLap);
    outBlur = stdLap.val[0] * stdLap.val[0];

    outBrightness = cv::mean(gray).val[0];

    std::vector<std::string> reasons;
    if (outBlur < config_.minBlurScore) {
        std::ostringstream ss;
        ss << "BLUR_DETECTED (score: " << std::fixed << std::setprecision(1) << outBlur << " < " << config_.minBlurScore << ")";
        reasons.push_back(ss.str());
    }
    if (outBrightness < config_.minBrightness) {
        reasons.push_back("IMAGE_TOO_DARK");
    } else if (outBrightness > config_.maxBrightness) {
        reasons.push_back("IMAGE_OVEREXPOSED");
    }

    if (reasons.empty()) {
        outMsg = "PASSED";
        return true;
    } else {
        std::string joined;
        for (size_t i = 0; i < reasons.size(); ++i) {
            if (i > 0) joined += " | ";
            joined += reasons[i];
        }
        outMsg = joined;
        return false;
    }
}

bool DigitalCompanionPipeline::detectCardCorners(const cv::Mat& image,
                                                 std::vector<cv::Point2f>& outSrcCorners,
                                                 std::vector<std::vector<cv::Point2f>>& outAllCorners,
                                                 std::vector<int>& outAllIds) const {
    cv::aruco::Dictionary dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_4X4_50);
    cv::aruco::DetectorParameters detectorParams;
    cv::aruco::ArucoDetector detector(dictionary, detectorParams);

    detector.detectMarkers(image, outAllCorners, outAllIds);
    if (outAllIds.empty()) {
        return false;
    }

    std::map<int, cv::Point2f> found;
    for (size_t i = 0; i < outAllIds.size(); ++i) {
        int id = outAllIds[i];
        const auto& c = outAllCorners[i];
        cv::Point2f center = (c[0] + c[1] + c[2] + c[3]) * 0.25f;
        found[id] = center;
    }

    int idTL = config_.idTopLeft;
    int idTR = config_.idTopRight;
    int idBR = config_.idBottomRight;
    int idBL = config_.idBottomLeft;

    if (found.find(idTL) == found.end() ||
        found.find(idTR) == found.end() ||
        found.find(idBR) == found.end() ||
        found.find(idBL) == found.end()) {
        return false;
    }

    outSrcCorners.clear();
    outSrcCorners.push_back(found[idTL]);
    outSrcCorners.push_back(found[idTR]);
    outSrcCorners.push_back(found[idBR]);
    outSrcCorners.push_back(found[idBL]);
    return true;
}

cv::Mat DigitalCompanionPipeline::warpCard(const cv::Mat& image, const std::vector<cv::Point2f>& srcCorners) const {
    std::vector<cv::Point2f> dstCorners = {
        config_.centerTopLeft,
        config_.centerTopRight,
        config_.centerBottomRight,
        config_.centerBottomLeft
    };

    cv::Mat M = cv::getPerspectiveTransform(srcCorners, dstCorners);
    cv::Mat warped;
    cv::warpPerspective(image, warped, M, cv::Size(config_.warpWidth, config_.warpHeight));
    return warped;
}

cv::Vec3d DigitalCompanionPipeline::extractRobustBgr(const cv::Mat& roi) const {
    if (roi.empty()) {
        return cv::Vec3d(0, 0, 0);
    }

    int totalPixels = roi.rows * roi.cols;
    std::vector<double> chB(totalPixels), chG(totalPixels), chR(totalPixels);

    int idx = 0;
    for (int y = 0; y < roi.rows; ++y) {
        const cv::Vec3b* ptr = roi.ptr<cv::Vec3b>(y);
        for (int x = 0; x < roi.cols; ++x) {
            chB[idx] = static_cast<double>(ptr[x][0]);
            chG[idx] = static_cast<double>(ptr[x][1]);
            chR[idx] = static_cast<double>(ptr[x][2]);
            idx++;
        }
    }

    std::sort(chB.begin(), chB.end());
    std::sort(chG.begin(), chG.end());
    std::sort(chR.begin(), chR.end());

    int lo = static_cast<int>(0.10 * totalPixels);
    int hi = static_cast<int>(0.90 * totalPixels);
    int count = (hi > lo) ? (hi - lo) : totalPixels;

    auto computeTrimmedMean = [&](const std::vector<double>& ch) -> double {
        double sum = 0.0;
        int start = (hi > lo) ? lo : 0;
        int end = (hi > lo) ? hi : static_cast<int>(ch.size());
        for (int i = start; i < end; ++i) {
            sum += ch[i];
        }
        return sum / count;
    };

    return cv::Vec3d(computeTrimmedMean(chB), computeTrimmedMean(chG), computeTrimmedMean(chR));
}

cv::Matx33d DigitalCompanionPipeline::solveCcm(const std::vector<cv::Vec3d>& observed,
                                              const std::vector<cv::Vec3d>& targets) const {
    int N = static_cast<int>(observed.size());
    cv::Mat O_t(N, 3, CV_64F);
    cv::Mat T_t(N, 3, CV_64F);

    for (int i = 0; i < N; ++i) {
        O_t.at<double>(i, 0) = observed[i][0];
        O_t.at<double>(i, 1) = observed[i][1];
        O_t.at<double>(i, 2) = observed[i][2];

        T_t.at<double>(i, 0) = targets[i][0];
        T_t.at<double>(i, 1) = targets[i][1];
        T_t.at<double>(i, 2) = targets[i][2];
    }

    cv::Mat Mt_mat(3, 3, CV_64F);
    cv::solve(O_t, T_t, Mt_mat, cv::DECOMP_SVD);

    cv::Mat M_mat = Mt_mat.t();
    cv::Matx33d M;
    for (int r = 0; r < 3; ++r) {
        for (int c = 0; c < 3; ++c) {
            M(r, c) = M_mat.at<double>(r, c);
        }
    }
    return M;
}

cv::Vec3d DigitalCompanionPipeline::applyCcm(const cv::Vec3d& bgr, const cv::Matx33d& M) const {
    cv::Vec3d out = M * bgr;
    out[0] = std::clamp(out[0], 0.0, 255.0);
    out[1] = std::clamp(out[1], 0.0, 255.0);
    out[2] = std::clamp(out[2], 0.0, 255.0);
    return out;
}

LabColor DigitalCompanionPipeline::bgrToLab(const cv::Vec3d& bgr) const {
    cv::Mat bgrMat(1, 1, CV_32FC3);
    bgrMat.at<cv::Vec3f>(0, 0) = cv::Vec3f(
        static_cast<float>(std::clamp(bgr[0] / 255.0, 0.0, 1.0)),
        static_cast<float>(std::clamp(bgr[1] / 255.0, 0.0, 1.0)),
        static_cast<float>(std::clamp(bgr[2] / 255.0, 0.0, 1.0))
    );

    cv::Mat labMat;
    cv::cvtColor(bgrMat, labMat, cv::COLOR_BGR2Lab);

    cv::Vec3f labVal = labMat.at<cv::Vec3f>(0, 0);
    return LabColor{
        static_cast<double>(labVal[0]),
        static_cast<double>(labVal[1]),
        static_cast<double>(labVal[2])
    };
}

FieldDrugTestingResult DigitalCompanionPipeline::process(const cv::Mat& inputImage, const std::string& outputDir) {
    FieldDrugTestingResult result;
    result.targetLab = config_.targetLab;

    if (inputImage.empty()) {
        result.status = "INCONCLUSIVE";
        result.confidence = 0.0;
        result.reason = "EMPTY_INPUT_IMAGE";
        return result;
    }

    // 1. Image Quality Control
    std::string qualityMsg;
    bool qualityOk = checkQuality(inputImage, result.blurScore, result.brightness, qualityMsg);
    if (!outputDir.empty()) {
        cv::imwrite(outputDir + "/01_input.jpg", inputImage);
    }

    if (!qualityOk) {
        result.status = "INCONCLUSIVE";
        result.confidence = 0.0;
        result.reason = "IMAGE_QUALITY_FAIL (" + qualityMsg + ")";
        if (!outputDir.empty()) {
            std::ofstream f(outputDir + "/result.json");
            f << result.toJsonString();
        }
        return result;
    }

    // 2. ArUco Detection
    std::vector<cv::Point2f> srcCorners;
    std::vector<std::vector<cv::Point2f>> allCorners;
    std::vector<int> allIds;
    bool cornersFound = detectCardCorners(inputImage, srcCorners, allCorners, allIds);
    result.markersFound = static_cast<int>(allIds.size());

    if (!outputDir.empty() && !allIds.empty()) {
        cv::Mat debugAruco = inputImage.clone();
        cv::aruco::drawDetectedMarkers(debugAruco, allCorners, allIds);
        cv::imwrite(outputDir + "/02_aruco_detected.jpg", debugAruco);
    }

    if (!cornersFound) {
        result.status = "INCONCLUSIVE";
        result.confidence = 0.0;
        result.reason = "CARD_NOT_FOUND (Missing required corner fiducials)";
        if (!outputDir.empty()) {
            std::ofstream f(outputDir + "/result.json");
            f << result.toJsonString();
        }
        return result;
    }

    // 3. Perspective Warp
    cv::Mat warped = warpCard(inputImage, srcCorners);
    if (!outputDir.empty()) {
        cv::imwrite(outputDir + "/03_warped.jpg", warped);
    }

    // 4. ROI Extraction
    std::vector<cv::Vec3d> observedRefBgr;
    for (const auto& r : config_.referenceRois) {
        cv::Mat patch = warped(r);
        observedRefBgr.push_back(extractRobustBgr(patch));
    }

    cv::Mat testPatch = warped(config_.testRoi);
    result.observedBgrRaw = extractRobustBgr(testPatch);

    // 5. Color Calibration Matrix (CCM)
    cv::Matx33d M_ccm = solveCcm(observedRefBgr, config_.referenceTargetBgr);
    result.observedBgrCalibrated = applyCcm(result.observedBgrRaw, M_ccm);

    // 6. CIELAB Conversion & CIEDE2000 Distance
    result.observedLab = bgrToLab(result.observedBgrCalibrated);
    result.deltaE00 = computeCIEDE2000(result.observedLab, config_.targetLab);

    // 7. Confidence Score & Tri-State Classification
    // if (confidence < 30%)              -> NEGATIVE
    // elif (confidence >= 30% && < 60%) -> INCONCLUSIVE
    // else (confidence >= 60%)           -> POSITIVE
    result.confidence = computeConfidence(result.deltaE00);

    if (result.confidence < 30.0) {
        result.status = "NEGATIVE";
        result.reason = "CONFIDENCE_LOW_NEGATIVE (confidence < 30%)";
    } else if (result.confidence < 60.0) {
        result.status = "INCONCLUSIVE";
        result.reason = "CONFIDENCE_BORDERLINE_INCONCLUSIVE (confidence in [30%-60%])";
    } else {
        result.status = "POSITIVE";
        result.reason = "CONFIDENCE_HIGH_POSITIVE (confidence >= 60%)";
    }

    // 8. Debug Overlays
    if (!outputDir.empty()) {
        cv::Mat debugRois = warped.clone();
        for (size_t i = 0; i < config_.referenceRois.size(); ++i) {
            const auto& r = config_.referenceRois[i];
            cv::rectangle(debugRois, r, cv::Scalar(0, 255, 0), 2);
            cv::putText(debugRois, "CAL " + std::to_string(i + 1), cv::Point(r.x + 5, r.y + 25),
                        cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 255, 0), 1, cv::LINE_AA);
        }
        cv::rectangle(debugRois, config_.testRoi, cv::Scalar(0, 0, 255), 3);
        cv::putText(debugRois, "TEST ZONE", cv::Point(config_.testRoi.x + 10, config_.testRoi.y + 30),
                    cv::FONT_HERSHEY_SIMPLEX, 0.6, cv::Scalar(0, 0, 255), 2, cv::LINE_AA);
        cv::imwrite(outputDir + "/04_rois.jpg", debugRois);

        std::ofstream f(outputDir + "/result.json");
        f << result.toJsonString();
    }

    return result;
}

} // namespace field_drug_testing

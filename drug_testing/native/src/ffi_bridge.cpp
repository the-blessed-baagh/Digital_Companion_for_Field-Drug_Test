#include "ffi_bridge.h"
#include "drug_testing_pipeline.hpp"

#include <opencv2/opencv.hpp>
#include <string>
#include <cstring>
#include <memory>

struct FdtResultHandle {
    field_drug_testing::FieldDrugTestingResult result;
    std::string status;
    std::string reason;
    std::string json;
};

extern "C" {

FdtResultHandle* fdt_process_image(const char* image_path, const char* output_dir) {
    if (image_path == nullptr || std::strlen(image_path) == 0) {
        return nullptr;
    }

    cv::Mat image = cv::imread(image_path);
    if (image.empty()) {
        return nullptr;
    }

    std::string outDir = (output_dir != nullptr) ? std::string(output_dir) : std::string("");

    field_drug_testing::FieldDrugTestingConfig config;
    field_drug_testing::DigitalCompanionPipeline pipeline(config);

    field_drug_testing::FieldDrugTestingResult cppResult = pipeline.process(image, outDir);

    auto* handle = new FdtResultHandle();
    handle->result = cppResult;
    handle->status = cppResult.status;
    handle->reason = cppResult.reason;
    handle->json = cppResult.toJsonString();

    return handle;
}

void fdt_free_result(FdtResultHandle* handle) {
    delete handle;
}

const char* fdt_get_status(const FdtResultHandle* handle) {
    if (handle == nullptr) return "INCONCLUSIVE";
    return handle->status.c_str();
}

const char* fdt_get_reason(const FdtResultHandle* handle) {
    if (handle == nullptr) return "Null handle";
    return handle->reason.c_str();
}

double fdt_get_confidence(const FdtResultHandle* handle) {
    if (handle == nullptr) return 0.0;
    return handle->result.confidence;
}

double fdt_get_delta_e00(const FdtResultHandle* handle) {
    if (handle == nullptr) return 999.0;
    return handle->result.deltaE00;
}

int fdt_get_markers_found(const FdtResultHandle* handle) {
    if (handle == nullptr) return 0;
    return handle->result.markersFound;
}

double fdt_get_blur_score(const FdtResultHandle* handle) {
    if (handle == nullptr) return 0.0;
    return handle->result.blurScore;
}

double fdt_get_brightness(const FdtResultHandle* handle) {
    if (handle == nullptr) return 0.0;
    return handle->result.brightness;
}

const char* fdt_get_json(const FdtResultHandle* handle) {
    if (handle == nullptr) return "{}";
    return handle->json.c_str();
}

} // extern "C"

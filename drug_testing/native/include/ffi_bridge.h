#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// Opaque result handle (caller must free with fdt_free_result)
typedef struct FdtResultHandle FdtResultHandle;

/**
 * Process a field drug test image.
 *
 * @param image_path  Absolute path to the captured JPG/PNG on device.
 * @param output_dir  Optional directory to write debug artifacts (can be NULL or empty).
 * @return            Opaque handle. Call fdt_get_* helpers, then fdt_free_result.
 *                    Returns NULL on hard failure (file not found, etc.).
 */
FdtResultHandle* fdt_process_image(const char* image_path, const char* output_dir);

/** Free the result handle and all associated memory. */
void fdt_free_result(FdtResultHandle* handle);

/** Status string: "POSITIVE", "NEGATIVE", or "INCONCLUSIVE". Never NULL if handle valid. */
const char* fdt_get_status(const FdtResultHandle* handle);

/** Human-readable reason / diagnostic message. */
const char* fdt_get_reason(const FdtResultHandle* handle);

/** Confidence percentage 0.0 – 100.0 */
double fdt_get_confidence(const FdtResultHandle* handle);

/** CIEDE2000 delta E value */
double fdt_get_delta_e00(const FdtResultHandle* handle);

/** Number of ArUco markers found (0–4) */
int fdt_get_markers_found(const FdtResultHandle* handle);

/** Blur score (Laplacian variance) */
double fdt_get_blur_score(const FdtResultHandle* handle);

/** Average brightness */
double fdt_get_brightness(const FdtResultHandle* handle);

/**
 * Full JSON string of the result (same format as C++ toJsonString()).
 * Valid only until fdt_free_result is called.
 */
const char* fdt_get_json(const FdtResultHandle* handle);

#ifdef __cplusplus
}
#endif

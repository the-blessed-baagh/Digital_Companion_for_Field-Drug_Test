#pragma once

#include <cmath>
#include <algorithm>

namespace field_drug_testing {

struct LabColor {
    double L;
    double a;
    double b;
};

/**
 * Computes ISO/CIE 11664-6:2014 / CIE 142-2001 CIEDE2000 color difference (Delta E 00).
 */
inline double computeCIEDE2000(const LabColor& c1, const LabColor& c2) {
    const double k_L = 1.0;
    const double k_C = 1.0;
    const double k_H = 1.0;
    const double PI = 3.14159265358979323846;
    const double DEG2RAD = PI / 180.0;
    const double RAD2DEG = 180.0 / PI;

    double C1 = std::hypot(c1.a, c1.b);
    double C2 = std::hypot(c2.a, c2.b);
    double Cbar = (C1 + C2) / 2.0;

    double Cbar7 = std::pow(Cbar, 7.0);
    double C25_7 = std::pow(25.0, 7.0);
    double G = 0.5 * (1.0 - std::sqrt(Cbar7 / (Cbar7 + C25_7)));

    double a1_prime = (1.0 + G) * c1.a;
    double a2_prime = (1.0 + G) * c2.a;

    double C1_prime = std::hypot(a1_prime, c1.b);
    double C2_prime = std::hypot(a2_prime, c2.b);

    auto compute_h_prime = [RAD2DEG](double a_p, double b) -> double {
        if (a_p == 0.0 && b == 0.0) return 0.0;
        double deg = std::atan2(b, a_p) * RAD2DEG;
        if (deg < 0.0) deg += 360.0;
        return deg;
    };

    double h1_prime = compute_h_prime(a1_prime, c1.b);
    double h2_prime = compute_h_prime(a2_prime, c2.b);

    double delta_L_prime = c2.L - c1.L;
    double delta_C_prime = C2_prime - C1_prime;

    double delta_h_prime = 0.0;
    if (C1_prime * C2_prime != 0.0) {
        double diff = h2_prime - h1_prime;
        if (std::abs(diff) <= 180.0) {
            delta_h_prime = diff;
        } else if (diff > 180.0) {
            delta_h_prime = diff - 360.0;
        } else {
            delta_h_prime = diff + 360.0;
        }
    }

    double delta_H_prime = 2.0 * std::sqrt(C1_prime * C2_prime) * std::sin((delta_h_prime / 2.0) * DEG2RAD);

    double Lbar_prime = (c1.L + c2.L) / 2.0;
    double Cbar_prime = (C1_prime + C2_prime) / 2.0;

    double hbar_prime = 0.0;
    if (C1_prime * C2_prime != 0.0) {
        double sum = h1_prime + h2_prime;
        double diff = std::abs(h1_prime - h2_prime);
        if (diff <= 180.0) {
            hbar_prime = sum / 2.0;
        } else if (sum < 360.0) {
            hbar_prime = (sum + 360.0) / 2.0;
        } else {
            hbar_prime = (sum - 360.0) / 2.0;
        }
    } else {
        hbar_prime = h1_prime + h2_prime;
    }

    double T = 1.0
        - 0.17 * std::cos((hbar_prime - 30.0) * DEG2RAD)
        + 0.24 * std::cos((2.0 * hbar_prime) * DEG2RAD)
        + 0.32 * std::cos((3.0 * hbar_prime + 6.0) * DEG2RAD)
        - 0.20 * std::cos((4.0 * hbar_prime - 63.0) * DEG2RAD);

    double delta_theta = 30.0 * std::exp(-std::pow((hbar_prime - 275.0) / 25.0, 2.0));
    double Cbar_prime7 = std::pow(Cbar_prime, 7.0);
    double R_C = 2.0 * std::sqrt(Cbar_prime7 / (Cbar_prime7 + C25_7));

    double S_L = 1.0 + (0.015 * std::pow(Lbar_prime - 50.0, 2.0)) / std::sqrt(20.0 + std::pow(Lbar_prime - 50.0, 2.0));
    double S_C = 1.0 + 0.045 * Cbar_prime;
    double S_H = 1.0 + 0.015 * Cbar_prime * T;

    double R_T = -std::sin(2.0 * delta_theta * DEG2RAD) * R_C;

    double term_L = delta_L_prime / (k_L * S_L);
    double term_C = delta_C_prime / (k_C * S_C);
    double term_H = delta_H_prime / (k_H * S_H);

    double delta_E = std::sqrt(
        term_L * term_L +
        term_C * term_C +
        term_H * term_H +
        R_T * term_C * term_H
    );

    return delta_E;
}

} // namespace field_drug_testing

// Compatibility namespace alias
//namespace kavach = field_drug_testing;

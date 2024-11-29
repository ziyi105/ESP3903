import matplotlib.pyplot as plt
import numpy as np
import math

# Constants
c = 3.00e8  # Speed of light in m/s
e = 1.602e-19  # Elementary charge in C
m = 1   # Diffraction order
d = 8.38528e-7  # Spacing of the diffraction grating in m
least_sq_bit = 5/(2**14) ##14bit resolution Arduino Board
sigma_arduino = 0.5*least_sq_bit

stopping_voltages_R = np.array([1.96, 1.98, 1.98, 1.98, 1.98, 1.99, 1.96, 1.98, 1.96, 1.98, 
                                1.96, 1.96, 1.97, 1.99, 1.98, 1.96, 1.97, 1.98, 1.97, 1.98, 
                                1.97, 1.97, 1.98, 1.97, 1.98])
mean_stopping_voltage_R = np.mean(stopping_voltages_R)
stdev_stopping_voltage_R = np.std(stopping_voltages_R, ddof=1)
sigma_h_values_R = []

h_values_R = np.array([6.3954e-34, 6.4604e-34, 6.4843e-34, 6.4742e-34, 6.4591e-34, 6.4853e-34, 6.4104e-34, 6.4761e-34, 6.4163e-34, 6.4572e-34, 
                        6.4234e-34, 6.3993e-34, 6.4474e-34, 6.4892e-34, 6.4591e-34, 6.4163e-34, 6.4274e-34, 6.4552e-34, 6.4454e-34, 6.4702e-34, 
                        6.4272e-34, 6.4274e-34, 6.4742e-34, 6.4425e-34,  6.4457e-34])  # Measured values of Planck's constant

mean_plancks_constant_R = np.mean(h_values_R)
stdev_plancks_constant_R = np.std(h_values_R, ddof=1)
print("Mean Planck's Constant (h):", mean_plancks_constant_R)
print("Standard Deviation of Planck's Constant (σ_h):", stdev_plancks_constant_R)

sigma_V_R = math.sqrt(stdev_stopping_voltage_R ** 2 + sigma_arduino **2)
# print(f"Uncertainty in Voltage : {sigma_V_R} m")

## Error of Spectrometer is -4.6degrees to -5.6degrees (Negative as it tilts to left side)
alpha_measured_R = np.radians(51.40)
beta_measured_R = np.radians(-2.06)
# Angular error range in degrees 
error_angle = np.radians(-5.1)
lambda_val_R = (d * (np.sin(alpha_measured_R) + np.sin(beta_measured_R))) / m
# Partial derivatives 
partial_lambda_alpha_R = (d * np.cos(alpha_measured_R)) / m 
partial_lambda_beta_R = (d * np.cos(alpha_measured_R)) / m
delta_lambda_R = np.sqrt((partial_lambda_alpha_R * error_angle) ** 2 + (partial_lambda_beta_R * error_angle) ** 2)
# print(f"Uncertainty in wavelength (σ_λ): {delta_lambda_R} m")

frequency_R = c / lambda_val_R
# print(f"Frequency of Red LED: {frequency_R} Hz")
sigma_f_R = (c * delta_lambda_R) / (lambda_val_R ** 2) #Uncertainty in frequency
# print(f"Calculated Wavelength (λ): {lambda_val_R:.3e} meters")
# print(f"Uncertainty in frequency (σ_f): {sigma_f_R} Hz")

# Error propagation formula for h uncertainty:
for idx, voltage in enumerate(stopping_voltages_R):
    # σ_h = sqrt((c / (e * λ) * σ_V)^2 + (c / (e * V) * σ_λ)^2)
    sigma_h = np.sqrt(((e * sigma_V_R) / frequency_R)**2 +
                      ((e * voltage * sigma_f_R) / (frequency_R **2 ))**2)
    # print(f"Planck's constant: ({h_values_R[idx]:.3e} ± {sigma_h:.3e}) J·s")
    sigma_h_values_R.append(sigma_h)
# print(f"Uncertainty in Planck's constant (σ_h): {sigma_h_values_R:} J·s")
# Known (accepted) value
h_known = 6.626e-34  # Known value of Planck's constant

# X-axis positions for each measurement
x_positions = np.arange(1, len(h_values_R) + 1)

# Plotting
plt.figure(figsize=(8, 6))

# Experimental values with error bars
plt.errorbar(x_positions, h_values_R, yerr=sigma_h_values_R, fmt='o', color='blue', label="Experimental Values (Red LED)")

# Accepted value as a horizontal line
plt.axhline(h_known, color='red', linestyle='--', label="Accepted Value")

# Labels and title
plt.xlabel("Measurement Index")
plt.ylabel("Planck's Constant (J·s)")
plt.title("Error Bar for Measurements of Planck's Constant for Red LED")

# Adjust y-axis limits to zoom in
plt.ylim(min(h_values_R) - 5 * max(sigma_h_values_R), max(h_values_R) + 5 * max(sigma_h_values_R))

# Legend
plt.legend()

# Show the plot
plt.show()

print(f"Fitted Planck's constant: {mean_plancks_constant_R:.3e} J·s")

#T-Test
from scipy import stats
import pandas as pd
t_stat_R, p_value_R = stats.ttest_1samp(h_values_R, h_known)
print(f"T-statistic: {t_stat_R:.3f}")
print(f"P-value: {p_value_R:.3f}")

#Bootstrap Method
from sklearn.utils import resample

n_iterations = 10000
bootstrap_means_R = []

for _ in range(n_iterations):
    sample = resample(h_values_R)
    bootstrap_means_R.append(np.mean(sample))

bootstrap_means_R = np.array(bootstrap_means_R)
confidence_level = 0.95
lower_bound_R = np.percentile(bootstrap_means_R, (1 - confidence_level) / 2 * 100)
upper_bound_R = np.percentile(bootstrap_means_R, (1 + confidence_level) / 2 * 100)

plt.figure(figsize=(8, 6))
plt.hist(bootstrap_means_R, bins=30, density=True, alpha=0.6, color='b', label="Bootstrap Means")
plt.axvline(lower_bound_R, color='r', linestyle='--', label=f"95% CI Lower Bound ({lower_bound_R:.3e})")
plt.axvline(upper_bound_R, color='r', linestyle='--', label=f"95% CI Upper Bound ({upper_bound_R:.3e})")
plt.xlabel("Mean Planck's Constant (J·s)")
plt.ylabel("Density")
plt.title("Bootstrap Distribution of Planck's Constant Mean")
plt.legend()
plt.show()

mean_bootstrap_R = np.mean(bootstrap_means_R)
print(f"Bootstrap Mean Planck's Constant: {mean_bootstrap_R:.3e} J·s")
print(f"95% Confidence Interval: {lower_bound_R:.3e} to {upper_bound_R:.3e} J·s")

# # Bootstrap Method for Standard Deviation
# from sklearn.utils import resample
# import numpy as np
# import matplotlib.pyplot as plt

# n_iterations = 10000
# bootstrap_stds_R = []

# for _ in range(n_iterations):
#     sample = resample(h_values_R)
#     bootstrap_stds_R.append(np.std(sample))

# bootstrap_stds_R = np.array(bootstrap_stds_R)
# confidence_level = 0.95
# lower_bound_R = np.percentile(bootstrap_stds_R, (1 - confidence_level) / 2 * 100)
# upper_bound_R = np.percentile(bootstrap_stds_R, (1 + confidence_level) / 2 * 100)

# plt.figure(figsize=(8, 6))
# plt.hist(bootstrap_stds_R, bins=30, density=True, alpha=0.6, color='b', label="Bootstrap Standard Deviations")
# plt.axvline(lower_bound_R, color='r', linestyle='--', label=f"95% CI Lower Bound ({lower_bound_R:.3e})")
# plt.axvline(upper_bound_R, color='r', linestyle='--', label=f"95% CI Upper Bound ({upper_bound_R:.3e})")
# plt.xlabel("Standard Deviation of Planck's Constant (J·s)")
# plt.ylabel("Density")
# plt.title("Bootstrap Distribution of Planck's Constant Standard Deviation")
# plt.legend()
# plt.show()

# mean_bootstrap_std_R = np.mean(bootstrap_stds_R)
# print(f"Bootstrap Mean Standard Deviation of Planck's Constant: {mean_bootstrap_std_R:.3e} J·s")
# print(f"95% Confidence Interval: {lower_bound_R:.3e} to {upper_bound_R:.3e} J·s")


data = { 
    "Stopping Voltage (V)": stopping_voltages_R, 
    "Planck's Constant (h)": h_values_R, 
    "Uncertainty in Planck's Constant (σ_h)": sigma_h_values_R, 
}
df_main = pd.DataFrame(data) 
# Summary statistics DataFrame 
summary_data = { 
    "Variable": ["Mean Planck's Constant", "Standard Deviation of Planck's Constant", 
    "Frequency (Hz)", "Uncertainty in Voltage (σ_V)", "Wavelength (λ)", "Uncertainty in Wavelength (σ_λ)", "Uncertainty in Frequency (σ_f)"], 
    "Value": [mean_plancks_constant_R, stdev_plancks_constant_R, frequency_R, sigma_V_R, lambda_val_R, delta_lambda_R, sigma_f_R],
    "Units": ["J·s", "J·s", "Hz", "V", "m", "m", "Hz"] } 
df_summary = pd.DataFrame(summary_data) 
print("Main Data:") 
print(df_main) 
print("\nSummary Statistics:") 
print(df_summary)
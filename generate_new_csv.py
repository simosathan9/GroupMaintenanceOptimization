import pandas as pd
import numpy as np

# Load your original CSV
input_file = "synthetic_maintenance_dataset.csv"
output_file = "synthetic_dataset.csv"

# Read data
df = pd.read_csv(input_file)

# Reduce PM durations (e.g. 40% to 60% of original value)
duration_scaling_factors = np.random.uniform(0.4, 0.6, size=len(df))
df['PM_duration'] = (df['PM_duration'] * duration_scaling_factors).clip(lower=0.25)

# Increase MTBF (e.g. 2x to 4x)
mtbf_scaling_factors = np.random.uniform(2.0, 4.0, size=len(df))
df['MTBF'] = df['MTBF'] * mtbf_scaling_factors

# Save new file
df.to_csv(output_file, index=False)

print(f"✅ New file saved as: {output_file}")
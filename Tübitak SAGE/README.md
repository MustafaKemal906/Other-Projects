# Half-Moon Sensor MTF Analysis

Python-based pipeline for estimating the **horizontal and vertical Modulation Transfer Function (MTF)** of an imaging sensor using two half-moon target captures.

The same straight-edge algorithm is independently applied to two physical measurements acquired at different orientations. The software automatically determines whether each result corresponds to the **X** or **Y** direction from the detected edge normal.

---

## Overview

The pipeline calculates:

- `MTF_X`
- `MTF_Y`
- ESF and LSF diagnostics
- MTF comparison plots
- MTF values in `lp/mm`
- Directional sensor performance

The basic processing chain is:

```text
Half-Moon Image
      ↓
ROI / Edge Detection
      ↓
Straight Edge Estimation
      ↓
Oversampled ESF
      ↓
LSF
      ↓
Fourier Transform
      ↓
MTF
      ↓
X / Y Assignment
```

---

## MTF Measurement Principle

For a valid straight edge, the **Edge Spread Function (ESF)** is extracted perpendicular to the detected edge.

The **Line Spread Function (LSF)** is obtained by differentiating the ESF:

\[
LSF(x)=\frac{d}{dx}ESF(x)
\]

The MTF is then calculated from the magnitude of the Fourier transform of the LSF:

\[
MTF(f)=
\left|
\mathcal{F}\{LSF(x)\}
\right|
\]

The result is normalized at zero spatial frequency:

\[
MTF(0)=1
\]

---

## Sensor Parameters

The current implementation uses:

```python
PIXEL_PITCH_MM = 0.017
```

Therefore:

```text
Pixel pitch = 0.017 mm = 17 µm
```

The corresponding sensor Nyquist frequency is:

\[
f_N=\frac{1}{2p}
\]

For a 17 µm pixel pitch:

\[
f_N \approx 29.41 \text{ lp/mm}
\]

---

## Input Data

The program expects two MATLAB `.mat` files containing two physical half-moon captures.

Example:

```text
capture_01.mat
capture_02.mat
```

The default MATLAB variable name is:

```text
img_final
```

---

## Usage

Basic usage:

```bash
python main.py first_capture.mat second_capture.mat
```

Example:

```bash
python main.py data/capture_01.mat data/capture_02.mat
```

The order of the input files does not determine X or Y.

The pipeline automatically assigns the measurements according to the detected edge normal.

---

## Command-Line Options

### Custom MAT key

```bash
python main.py first.mat second.mat --mat-key image
```

Default:

```text
img_final
```

### Disable MATLAB v7.3 / HDF5 transpose

```bash
python main.py first.mat second.mat --no-hdf5-transpose
```

### Run without graphs

```bash
python main.py first.mat second.mat --no-graphs
```

---

## Main Application

```python
import argparse

from src.variables import ImageData
from src.mtf_pipeline import MTFPipeline
from src.graph import Graph
```

Input data are stored in `ImageData`:

```python
data = ImageData(
    data_path=path,
    mat_key=mat_key,
    mat_hdf5_transpose=hdf5_transpose,
    pixel_pitch_mm=PIXEL_PITCH_MM,
)
```

The complete X/Y analysis is executed by:

```python
pipeline = MTFPipeline()

results = pipeline.run_xy(
    data_a,
    data_b,
)
```

Results are accessed as:

```python
x_data = results["x"]["data"]
y_data = results["y"]["data"]
```

---

## Graph Outputs

Diagnostic plots for the X direction:

```python
graph.show_all_for_axis(
    x_data,
    "MTF_X",
)
```

Diagnostic plots for the Y direction:

```python
graph.show_all_for_axis(
    y_data,
    "MTF_Y",
)
```

Final X/Y comparison:

```python
graph.plot_xy_comparison(
    x_data,
    y_data,
)
```

Summary plot:

```python
graph.plot_xy_summary_bar(
    x_data,
    y_data,
)
```

---

## Why Two Captures?

A straight-edge measurement primarily characterizes the MTF in the direction perpendicular to that edge.

Two physically rotated half-moon captures are therefore used to measure the sensor response in two orthogonal directions.

```text
Capture A
   ↓
Edge Detection
   ↓
Edge Normal
   ↓
MTF in one sensor direction


Capture B
   ↓
Edge Detection
   ↓
Edge Normal
   ↓
MTF in the orthogonal direction
```

The software automatically assigns the measurements to:

```text
MTF_X
MTF_Y
```

---

## Why a Half-Moon Target?

The half-moon target contains a locally straight edge that can be used for edge-based MTF estimation.

Instead of treating the complete target image as the system PSF, the algorithm analyzes the straight-edge region.

The resulting pipeline is:

```text
Edge
 ↓
ESF
 ↓
LSF
 ↓
FFT
 ↓
MTF
```

This helps separate the edge response from the finite geometry of the complete target.

---

## Project Structure

```text
project/
│
├── main.py
│
└── src/
    ├── variables.py
    ├── mtf_pipeline.py
    ├── graph.py
    └── ...
```

### `ImageData`

Stores:

- input file path
- MAT variable name
- MATLAB/HDF5 transpose configuration
- pixel pitch

### `MTFPipeline`

Controls:

- image processing
- edge analysis
- directional assignment
- MTF calculation
- X/Y result generation

### `Graph`

Handles:

- diagnostic plots
- ESF plots
- LSF plots
- MTF curves
- X/Y comparison plots
- summary visualization

---

## Important Considerations

Reliable edge-based MTF measurement requires a sufficiently valid straight-edge region.

Possible error sources include:

- edge curvature
- low signal-to-noise ratio
- target halo
- background non-uniformity
- inaccurate edge localization
- saturation
- insufficient sampling
- incorrect pixel pitch
- non-ideal target geometry

For this reason, the diagnostic outputs should be evaluated together with the final MTF curve.

---

## Example Workflow

```text
1. Acquire two half-moon images
                ↓
2. Load MAT images
                ↓
3. Detect the target
                ↓
4. Find the straight edge
                ↓
5. Determine edge orientation
                ↓
6. Assign X / Y direction
                ↓
7. Generate oversampled ESF
                ↓
8. Differentiate ESF → LSF
                ↓
9. Fourier transform LSF
                ↓
10. Convert frequency to lp/mm
                ↓
11. Report MTF_X and MTF_Y
```

---

## Example Commands

```bash
python main.py \
    data/halfmoon_horizontal.mat \
    data/halfmoon_vertical.mat
```

Terminal-only analysis:

```bash
python main.py \
    data/halfmoon_horizontal.mat \
    data/halfmoon_vertical.mat \
    --no-graphs
```

Custom MAT key:

```bash
python main.py \
    data/capture_a.mat \
    data/capture_b.mat \
    --mat-key img_final
```

---

## Goal

The goal of this project is to provide a repeatable and physically interpretable method for evaluating directional sensor image quality.

The final outputs are:

\[
MTF_X(f)
\]

and

\[
MTF_Y(f)
\]

expressed in physical spatial-frequency units:

```text
lp/mm
```

---

## Reference

Glenn D. Boreman,  
*Modulation Transfer Function in Optical and Electro-Optical Systems*,  
Second Edition, SPIE Press, 2021.

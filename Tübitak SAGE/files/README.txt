HALF-MOON MTF_X + MTF_Y — FULL PACKAGE
=======================================

Architecture
------------
main.py
src/
    __init__.py
    variables.py
    mtf_pipeline.py
    graph.py

Basis
-----
The MTF calculation inside mtf_pipeline.py is the same straight-edge
half-moon algorithm supplied by the user:

MAT
 -> global background
 -> half-moon ROI
 -> long straight diameter edge by RANSAC
 -> subpixel edge refinement
 -> curvature / straightness checks
 -> 8x oversampled ESF
 -> numerical LSF
 -> tail baseline removal
 -> small Tukey end taper
 -> FFT
 -> numerical derivative correction
 -> lp/mm
 -> MTF @ 10 lp/mm
 -> MTF @ Nyquist
 -> MTF50
 -> MTF10
 -> quality gates

X / Y
-----
The SAME pipeline is run independently on TWO physical MAT captures.

MTF_X:
    fitted MTF normal approximately 0/180 degrees relative to sensor X.

MTF_Y:
    fitted MTF normal approximately 90 degrees relative to sensor X.

The two input files can be supplied in either order.
The program assigns X/Y automatically from the fitted edge-normal direction.

No software image rotation is used.
No curved-edge MTF is used.
No X/Y decomposition from a single slanted edge is used.

Run
---
Install:
    uv sync

Normal:
    uv run main.py X_CAPTURE.mat Y_CAPTURE.mat

Different MAT key:
    uv run main.py X_CAPTURE.mat Y_CAPTURE.mat --mat-key image

Terminal only:
    uv run main.py X_CAPTURE.mat Y_CAPTURE.mat --no-graphs

MATLAB v7.3 without automatic transpose:
    uv run main.py X_CAPTURE.mat Y_CAPTURE.mat --no-hdf5-transpose

Terminal final block
--------------------
FINAL SENSOR X / Y MTF

    MTF_X @ 10 lp/mm
    MTF_X @ Nyquist
    MTF50_X
    MTF10_X
    MTF_X quality

    MTF_Y @ 10 lp/mm
    MTF_Y @ Nyquist
    MTF50_Y
    MTF10_Y
    MTF_Y quality

Graphs
------
For BOTH X and Y:
1. Original MAT image
2. Background-subtracted image
3. ROI + fitted straight edge
4. Subpixel straight-edge residuals
5. Oversampled ESF
6. LSF
7. MTF in lp/mm

Final:
8. MTF_X and MTF_Y on the same graph
9. Bar comparison of MTF @ 10 lp/mm and MTF @ Nyquist

Sensor
------
Pixel pitch:
    0.017 mm / pixel

Sensor Nyquist:
    29.4118 lp/mm

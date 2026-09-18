from dataclasses import dataclass, field

import numpy as np


@dataclass
class ImageData:
    # Input
    data_path: str
    mat_key: str = "img_final"
    mat_hdf5_transpose: bool = True
    pixel_pitch_mm: float = 0.017

    # Filled automatically after load
    width: int | None = None
    height: int | None = None

    # Image / background
    intensity: np.ndarray | None = None
    background_subtracted: np.ndarray | None = None

    global_background_dn: float | None = None
    global_background_sigma_dn: float | None = None

    # ROI
    roi_raw: np.ndarray | None = None
    roi: np.ndarray | None = None
    roi_origin_xy: tuple[int, int] | None = None

    local_background_plane: np.ndarray | None = None
    local_background_sigma_dn: float | None = None

    # Straight edge
    edge_points_xy: np.ndarray | None = None
    edge_ransac_inliers_xy: np.ndarray | None = None
    edge_refined_points_xy: np.ndarray | None = None

    edge_normal_xy: tuple[float, float] | None = None
    edge_tangent_xy: tuple[float, float] | None = None
    edge_center_xy: tuple[float, float] | None = None
    edge_rho_px: float | None = None

    edge_line_rmse_px: float | None = None
    edge_span_px: float | None = None
    edge_slant_deg: float | None = None
    edge_normal_angle_deg: float | None = None

    curvature_sag_px: float | None = None
    quadratic_improvement: float | None = None

    phase_coverage: float | None = None
    valid_profiles: int | None = None

    # ESF
    esf_d_px: np.ndarray | None = None
    esf_signal: np.ndarray | None = None
    esf_counts: np.ndarray | None = None

    bright_level_dn: float | None = None
    dark_level_dn: float | None = None
    bright_sigma_dn: float | None = None
    dark_sigma_dn: float | None = None
    cnr: float | None = None

    # LSF
    lsf_d_px: np.ndarray | None = None
    lsf_signal: np.ndarray | None = None
    lsf_endpoint_ratio: float | None = None

    # MTF
    mtf_freq_cpp: np.ndarray | None = None
    mtf_freq_lpmm: np.ndarray | None = None
    mtf_signal: np.ndarray | None = None

    nyquist_lpmm: float | None = None
    mtf_at_10_lpmm: float | None = None
    mtf_at_nyquist: float | None = None
    mtf50_lpmm: float | None = None
    mtf10_lpmm: float | None = None

    # Quality
    quality_status: str | None = None
    quality_warnings: list[str] = field(
        default_factory=list
    )

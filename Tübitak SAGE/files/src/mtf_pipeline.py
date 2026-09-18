import numpy as np
from pathlib import Path
from scipy.io import loadmat

from scipy.ndimage import (
    gaussian_filter,
    label,
    map_coordinates,
)
from scipy.signal import savgol_filter
from scipy.signal.windows import tukey


class MTFPipeline:
    """
    Half-moon / semicircular target MTF from MATLAB image data.

    The curved arc is NOT used for MTF.

    The algorithm automatically detects the long straight diameter edge
    of the half-moon target, rejects the curved arc/end-corners, and then
    performs an ISO-12233-like slanted-edge measurement:

        straight edge
          -> subpixel line
          -> oversampled ESF
          -> LSF
          -> FFT
          -> system MTF

    The resulting MTF already contains the detector pixel-aperture response,
    because it is measured directly from the sampled edge image.
    """

    # ==========================================================
    # 1) MATLAB MAT
    # ==========================================================
    def load_mat_image(self, data):
        """
        Load a 2-D image matrix from a MATLAB .mat file.

        Supported:
          - MATLAB v4/v5/v6/v7-v7.2 via scipy.io.loadmat
          - MATLAB v7.3/HDF5 via h5py fallback

        Default variable name:
            img_final

        No normalization is applied. The original numeric values are used.
        """
        path = Path(
            data.data_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"MAT dosyası bulunamadı: {path}"
            )

        key = str(
            data.mat_key
        )

        arr = None
        backend = None

        # Standard MAT files up to v7.2.
        try:
            mat = loadmat(
                path,
                variable_names=[key],
            )

            if key not in mat:
                # Load metadata for a useful error message.
                mat_all = loadmat(
                    path
                )

                available = [
                    k
                    for k in mat_all.keys()
                    if not k.startswith("__")
                ]

                raise KeyError(
                    f"MAT içinde '{key}' anahtarı yok. "
                    f"Mevcut değişkenler: {available}"
                )

            arr = mat[key]
            backend = "scipy.io.loadmat"

        except (
            NotImplementedError,
            OSError,
            ValueError,
        ) as exc:
            # MATLAB v7.3 is HDF5.
            try:
                import h5py
            except ImportError as h5_exc:
                raise RuntimeError(
                    "Bu MAT dosyası MATLAB v7.3/HDF5 olabilir. "
                    "h5py kurulmalı: uv add h5py"
                ) from h5_exc

            try:
                with h5py.File(
                    path,
                    "r",
                ) as f:
                    if key not in f:
                        available = list(
                            f.keys()
                        )

                        raise KeyError(
                            f"MAT v7.3 içinde '{key}' anahtarı yok. "
                            f"Mevcut kök anahtarlar: {available}"
                        )

                    arr = np.asarray(
                        f[key][()]
                    )

            except OSError:
                raise exc

            if (
                getattr(
                    data,
                    "mat_hdf5_transpose",
                    True,
                )
                and arr.ndim == 2
            ):
                arr = arr.T

            backend = "h5py (MATLAB v7.3)"

        arr = np.asarray(
            arr
        )

        arr = np.squeeze(
            arr
        )

        if arr.ndim != 2:
            raise ValueError(
                f"'{key}' 2-D görüntü matrisi olmalı; "
                f"gelen shape={arr.shape}"
            )

        if not np.issubdtype(
            arr.dtype,
            np.number,
        ):
            raise TypeError(
                f"'{key}' sayısal değil: dtype={arr.dtype}"
            )

        if np.iscomplexobj(
            arr
        ):
            raise TypeError(
                f"'{key}' complex veri içeriyor."
            )

        if not np.all(
            np.isfinite(arr)
        ):
            raise ValueError(
                f"'{key}' NaN/Inf içeriyor."
            )

        # Preserve original dynamic range but use float for processing.
        img = arr.astype(
            float,
            copy=False,
        )

        data.intensity = (
            img
        )

        data.height, data.width = map(
            int,
            img.shape,
        )

        print("\n========== MAT YÜKLENDİ ==========")
        print(f"Dosya   : {data.data_path}")
        print(f"Backend : {backend}")
        print(f"Anahtar : {key}")
        print(
            f"Boyut   : "
            f"{data.width}x{data.height}"
        )
        print(
            f"dtype   : "
            f"{arr.dtype}"
        )
        print(
            f"min/max : "
            f"{np.min(img):.3f} / "
            f"{np.max(img):.3f}"
        )
        print("=================================\n")

    # Backward-friendly alias.
    def load_raw_image(self, data):
        return self.load_mat_image(
            data
        )

    # ==========================================================
    # 2) GLOBAL BACKGROUND
    # ==========================================================
    @staticmethod
    def _robust_sigma(values):
        v = np.asarray(
            values,
            dtype=float,
        )

        med = float(
            np.median(v)
        )

        return (
            1.4826
            * float(
                np.median(
                    np.abs(v-med)
                )
            )
        )

    def subtract_background(
        self,
        data,
        border_fraction=0.08,
    ):
        """
        Only a global background level is removed.
        No radius mask. No target pixels are zeroed.
        """
        if data.intensity is None:
            raise ValueError(
                "Önce load_raw_image() çalıştırılmalı."
            )

        img = np.asarray(
            data.intensity,
            dtype=float,
        )

        h, w = img.shape

        band = max(
            6,
            int(
                round(
                    min(h, w)
                    * border_fraction
                )
            ),
        )

        border = np.concatenate([
            img[:band, :].ravel(),
            img[-band:, :].ravel(),
            img[:, :band].ravel(),
            img[:, -band:].ravel(),
        ])

        bg = float(
            np.median(border)
        )

        sigma = float(
            self._robust_sigma(
                border
            )
        )

        data.global_background_dn = (
            bg
        )

        data.global_background_sigma_dn = (
            sigma
        )

        data.background_subtracted = (
            img-bg
        )

        print("========== GLOBAL BACKGROUND ==========")
        print(f"Border median              : {bg:.3f} DN")
        print(f"Border robust sigma        : {sigma:.3f} DN")
        print("Hard radius mask           : YOK")
        print("======================================\n")

    # ==========================================================
    # 3) HALF-MOON ROI
    # ==========================================================
    @staticmethod
    def _largest_component(mask):
        labels, n = label(
            mask
        )

        if n <= 0:
            return None

        sizes = np.bincount(
            labels.ravel()
        )

        sizes[0] = 0

        idx = int(
            np.argmax(sizes)
        )

        if sizes[idx] <= 0:
            return None

        return (
            labels == idx
        )

    @staticmethod
    def _fit_border_plane(
        roi,
        border_fraction=0.12,
        iterations=7,
    ):
        img = np.asarray(
            roi,
            dtype=float,
        )

        h, w = img.shape

        b = max(
            4,
            int(
                round(
                    min(h, w)
                    * border_fraction
                )
            ),
        )

        mask = np.zeros(
            img.shape,
            dtype=bool,
        )

        mask[:b, :] = True
        mask[-b:, :] = True
        mask[:, :b] = True
        mask[:, -b:] = True

        y, x = np.indices(
            img.shape,
            dtype=float,
        )

        xx = x[mask].ravel()
        yy = y[mask].ravel()
        zz = img[mask].ravel()

        keep = np.ones(
            zz.size,
            dtype=bool,
        )

        coef = np.array([
            np.median(zz),
            0.0,
            0.0,
        ], dtype=float)

        for _ in range(iterations):
            A = np.column_stack([
                np.ones(
                    np.count_nonzero(keep)
                ),
                xx[keep],
                yy[keep],
            ])

            coef, *_ = np.linalg.lstsq(
                A,
                zz[keep],
                rcond=None,
            )

            pred = (
                coef[0]
                + coef[1]*xx
                + coef[2]*yy
            )

            resid = (
                zz-pred
            )

            med = float(
                np.median(
                    resid[keep]
                )
            )

            sigma = max(
                MTFPipeline._robust_sigma(
                    resid[keep]
                ),
                1e-12,
            )

            new_keep = (
                np.abs(
                    resid-med
                )
                <= 3.5*sigma
            )

            if np.array_equal(
                new_keep,
                keep,
            ):
                break

            keep = new_keep

        plane = (
            coef[0]
            + coef[1]*x
            + coef[2]*y
        )

        sigma = float(
            MTFPipeline._robust_sigma(
                img[mask]
                - plane[mask]
            )
        )

        return (
            plane,
            coef,
            sigma,
        )

    def crop_roi(
        self,
        data,
        threshold_fraction=0.18,
        margin_px=28,
        min_size=96,
        max_size=240,
    ):
        """
        Auto-crop the bright half-moon component with enough dark margin
        around it for edge plateaus.
        """
        if data.background_subtracted is None:
            raise ValueError(
                "Önce subtract_background() çalıştırılmalı."
            )

        img = np.asarray(
            data.background_subtracted,
            dtype=float,
        )

        peak = float(
            np.max(img)
        )

        if peak <= 0:
            raise RuntimeError(
                "Pozitif half-moon target bulunamadı."
            )

        threshold = max(
            threshold_fraction*peak,
            4.0
            * max(
                data.global_background_sigma_dn
                or 0.0,
                1e-12,
            ),
        )

        component = self._largest_component(
            img >= threshold
        )

        if (
            component is None
            or np.count_nonzero(component) < 20
        ):
            raise RuntimeError(
                "Yarım-ay hedef için yeterli bağlı parlak alan bulunamadı."
            )

        yy, xx = np.nonzero(
            component
        )

        x0_obj = int(
            np.min(xx)
        )
        x1_obj = int(
            np.max(xx)
        ) + 1

        y0_obj = int(
            np.min(yy)
        )
        y1_obj = int(
            np.max(yy)
        ) + 1

        cx = 0.5*(
            x0_obj+x1_obj-1
        )

        cy = 0.5*(
            y0_obj+y1_obj-1
        )

        obj_w = (
            x1_obj-x0_obj
        )

        obj_h = (
            y1_obj-y0_obj
        )

        size = int(
            np.ceil(
                max(
                    obj_w,
                    obj_h,
                    min_size
                )
                + 2*margin_px
            )
        )

        size = int(
            np.clip(
                size,
                min_size,
                max_size,
            )
        )

        if size % 2 == 0:
            size += 1

        half = size//2

        x0 = int(
            round(cx)
        ) - half

        x1 = (
            x0+size
        )

        y0 = int(
            round(cy)
        ) - half

        y1 = (
            y0+size
        )

        # Shift ROI rather than truncating it.
        if x0 < 0:
            x1 -= x0
            x0 = 0

        if y0 < 0:
            y1 -= y0
            y0 = 0

        if x1 > img.shape[1]:
            shift = (
                x1-img.shape[1]
            )
            x0 -= shift
            x1 = img.shape[1]

        if y1 > img.shape[0]:
            shift = (
                y1-img.shape[0]
            )
            y0 -= shift
            y1 = img.shape[0]

        if (
            x0 < 0
            or y0 < 0
            or x1 > img.shape[1]
            or y1 > img.shape[0]
        ):
            raise RuntimeError(
                "Auto ROI görüntü sınırlarına sığmıyor."
            )

        # Use original DN inside ROI and fit a local plane from the border.
        roi_raw = np.asarray(
            data.intensity[
                y0:y1,
                x0:x1,
            ],
            dtype=float,
        ).copy()

        plane, coef, sigma = (
            self._fit_border_plane(
                roi_raw
            )
        )

        roi = (
            roi_raw-plane
        )

        data.roi_raw = (
            roi_raw
        )

        data.roi = (
            roi
        )

        data.roi_origin_xy = (
            x0,
            y0,
        )

        data.local_background_plane = (
            plane
        )

        data.local_background_sigma_dn = (
            sigma
        )

        print("========== HALF-MOON ROI ==========")
        print(
            f"Target component bbox      : "
            f"{obj_w}x{obj_h} px"
        )
        print(
            f"ROI origin                 : "
            f"({x0},{y0})"
        )
        print(
            f"ROI size                   : "
            f"{roi.shape[1]}x{roi.shape[0]} px"
        )
        print(
            f"Local plane a              : "
            f"{coef[0]:.3f} DN"
        )
        print(
            f"Local plane bx             : "
            f"{coef[1]:+.5f} DN/px"
        )
        print(
            f"Local plane by             : "
            f"{coef[2]:+.5f} DN/px"
        )
        print(
            f"Local background sigma     : "
            f"{sigma:.3f} DN"
        )
        print("=================================\n")

    # ==========================================================
    # 4) LONG STRAIGHT DIAMETER EDGE
    # ==========================================================
    @staticmethod
    def _line_from_two_points(
        p1,
        p2,
    ):
        """
        Return unit normal n=(nx,ny), tangent t=(tx,ty), rho
        for line n dot p = rho.
        """
        v = (
            np.asarray(p2, dtype=float)
            - np.asarray(p1, dtype=float)
        )

        norm = float(
            np.hypot(
                v[0],
                v[1],
            )
        )

        if norm <= 1e-12:
            return None

        t = (
            v/norm
        )

        n = np.array([
            -t[1],
            t[0],
        ], dtype=float)

        rho = float(
            np.dot(
                n,
                p1,
            )
        )

        return (
            n,
            t,
            rho,
        )

    @staticmethod
    def _canonical_line(
        n,
        t,
        rho,
    ):
        """
        Keep tangent angle in [0,180) for stable reporting.
        """
        n = np.asarray(
            n,
            dtype=float,
        )

        t = np.asarray(
            t,
            dtype=float,
        )

        angle = (
            np.degrees(
                np.arctan2(
                    t[1],
                    t[0],
                )
            )
            % 180.0
        )

        if angle >= 180.0:
            angle -= 180.0

        return (
            n,
            t,
            float(rho),
        )

    @staticmethod
    def _weighted_tls_line(
        points_xy,
        base_weights=None,
        iterations=7,
    ):
        pts = np.asarray(
            points_xy,
            dtype=float,
        )

        if len(pts) < 3:
            raise RuntimeError(
                "TLS line fit için yeterli nokta yok."
            )

        if base_weights is None:
            base = np.ones(
                len(pts),
                dtype=float,
            )
        else:
            base = np.asarray(
                base_weights,
                dtype=float,
            ).copy()

        robust = np.ones(
            len(pts),
            dtype=float,
        )

        for _ in range(iterations):
            w = np.clip(
                base*robust,
                1e-12,
                None,
            )

            w = (
                w/np.sum(w)
            )

            c = np.sum(
                pts*w[:, None],
                axis=0,
            )

            q = (
                pts-c
            )

            C = (
                q.T
                @ (
                    q*w[:, None]
                )
            )

            eigval, eigvec = np.linalg.eigh(
                C
            )

            t = eigvec[
                :,
                int(
                    np.argmax(eigval)
                )
            ]

            t = (
                t/np.linalg.norm(t)
            )

            n = np.array([
                -t[1],
                t[0],
            ])

            rho = float(
                np.dot(
                    n,
                    c,
                )
            )

            resid = (
                pts@n-rho
            )

            sigma = max(
                MTFPipeline._robust_sigma(
                    resid
                ),
                1e-6,
            )

            u = np.abs(
                resid
            ) / (
                1.5*sigma
            )

            robust_new = np.ones_like(
                u
            )

            mask = (
                u > 1.0
            )

            robust_new[mask] = (
                1.0/u[mask]
            )

            if np.max(
                np.abs(
                    robust_new-robust
                )
            ) < 1e-3:
                robust = robust_new
                break

            robust = (
                robust_new
            )

        return (
            n,
            t,
            rho,
            c,
            resid,
        )

    def detect_straight_edge(
        self,
        data,
        smooth_sigma=0.85,
        gradient_percentile=82.0,
        ransac_iterations=5000,
        inlier_threshold_px=0.75,
        random_seed=12,
    ):
        """
        RANSAC searches for the longest coherent straight gradient segment.
        This rejects the curved semicircular arc because a long chord has
        much larger line span than a locally tangent piece of the arc.
        """
        if data.roi is None:
            raise ValueError(
                "Önce crop_roi() çalıştırılmalı."
            )

        img = np.asarray(
            data.roi,
            dtype=float,
        )

        sm = gaussian_filter(
            img,
            sigma=smooth_sigma,
            mode="nearest",
        )

        gy, gx = np.gradient(
            sm
        )

        mag = np.hypot(
            gx,
            gy,
        )

        h, w = img.shape

        # Exclude ROI border from line search.
        valid_area = np.ones(
            img.shape,
            dtype=bool,
        )

        border = max(
            3,
            int(
                round(
                    0.04*min(h, w)
                )
            ),
        )

        valid_area[:border, :] = False
        valid_area[-border:, :] = False
        valid_area[:, :border] = False
        valid_area[:, -border:] = False

        values = mag[
            valid_area
        ]

        threshold = float(
            np.percentile(
                values,
                gradient_percentile,
            )
        )

        edge_mask = (
            valid_area
            & (mag >= threshold)
        )

        yy, xx = np.nonzero(
            edge_mask
        )

        points = np.column_stack([
            xx.astype(float),
            yy.astype(float),
        ])

        weights = mag[
            edge_mask
        ].astype(float)

        if len(points) < 40:
            raise RuntimeError(
                "Straight-edge detection için yeterli gradient noktası yok."
            )

        # Limit RANSAC population to strongest points if necessary.
        max_points = 3500

        if len(points) > max_points:
            order = np.argsort(
                weights
            )[
                -max_points:
            ]

            points = points[order]
            weights = weights[order]

        rng = np.random.default_rng(
            random_seed
        )

        best = None

        diag = float(
            np.hypot(
                w,
                h,
            )
        )

        for _ in range(
            int(ransac_iterations)
        ):
            i, j = rng.choice(
                len(points),
                size=2,
                replace=False,
            )

            line = self._line_from_two_points(
                points[i],
                points[j],
            )

            if line is None:
                continue

            n, t, rho = line

            dist = np.abs(
                points@n-rho
            )

            inliers = (
                dist
                <= inlier_threshold_px
            )

            nin = int(
                np.count_nonzero(
                    inliers
                )
            )

            if nin < 18:
                continue

            s = (
                points[inliers]@t
            )

            span = float(
                np.percentile(
                    s,
                    97.0,
                )
                - np.percentile(
                    s,
                    3.0,
                )
            )

            # The straight diameter should be a long segment.
            if span < (
                0.25
                * min(h, w)
            ):
                continue

            weighted_support = float(
                np.sum(
                    weights[inliers]
                )
            )

            score = (
                weighted_support
                * (
                    span/diag
                )**1.35
            )

            if (
                best is None
                or score > best["score"]
            ):
                best = {
                    "score": score,
                    "n": n,
                    "t": t,
                    "rho": rho,
                    "inliers": inliers,
                    "span": span,
                }

        if best is None:
            raise RuntimeError(
                "Yarım-ay hedefte uzun düz çap kenarı bulunamadı."
            )

        # Robust TLS on RANSAC inliers.
        inlier_points = points[
            best["inliers"]
        ]

        inlier_weights = weights[
            best["inliers"]
        ]

        (
            n,
            t,
            rho,
            center,
            resid,
        ) = self._weighted_tls_line(
            inlier_points,
            inlier_weights,
        )

        n, t, rho = (
            self._canonical_line(
                n,
                t,
                rho,
            )
        )

        # Store raw detector points.
        data.edge_points_xy = (
            points
        )

        data.edge_ransac_inliers_xy = (
            inlier_points
        )

        # ------------------------------------------------------
        # Subpixel refinement from gradient centroid
        # ------------------------------------------------------
        p0 = (
            rho*n
        )

        s_in = (
            inlier_points@t
        )

        s_lo = float(
            np.percentile(
                s_in,
                6.0,
            )
        )

        s_hi = float(
            np.percentile(
                s_in,
                94.0,
            )
        )

        # Keep endpoints away from the curved arc corners.
        trim = (
            0.10
            * (s_hi-s_lo)
        )

        s_lo += trim
        s_hi -= trim

        sample_s = np.arange(
            s_lo,
            s_hi+0.5,
            1.0,
        )

        d_probe = np.arange(
            -2.75,
            2.75+0.025,
            0.05,
        )

        refined = []

        for s0 in sample_s:
            base = (
                p0+s0*t
            )

            xxq = (
                base[0]
                + d_probe*n[0]
            )

            yyq = (
                base[1]
                + d_probe*n[1]
            )

            inside = (
                (xxq >= 1.0)
                & (xxq <= w-2.0)
                & (yyq >= 1.0)
                & (yyq <= h-2.0)
            )

            if np.count_nonzero(
                inside
            ) < 30:
                continue

            vals = map_coordinates(
                mag,
                np.vstack([
                    yyq[inside],
                    xxq[inside],
                ]),
                order=1,
                mode="nearest",
            )

            dd = d_probe[
                inside
            ]

            baseline = float(
                np.percentile(
                    vals,
                    20.0,
                )
            )

            wwq = np.clip(
                vals-baseline,
                0.0,
                None,
            )

            if np.sum(wwq) <= 0:
                continue

            # Focus on the dominant edge peak.
            strong = (
                wwq
                >= 0.20*np.max(wwq)
            )

            if np.count_nonzero(
                strong
            ) < 3:
                continue

            delta = float(
                np.sum(
                    dd[strong]
                    * wwq[strong]
                )
                / np.sum(
                    wwq[strong]
                )
            )

            q = (
                base
                + delta*n
            )

            refined.append(
                q
            )

        refined = np.asarray(
            refined,
            dtype=float,
        )

        if len(refined) < 20:
            raise RuntimeError(
                "Subpixel straight-edge refinement için yeterli profil yok."
            )

        (
            n2,
            t2,
            rho2,
            center2,
            residual2,
        ) = self._weighted_tls_line(
            refined
        )

        n2, t2, rho2 = (
            self._canonical_line(
                n2,
                t2,
                rho2,
            )
        )

        # Ensure tangent orientation is consistent.
        if np.dot(
            t2,
            t,
        ) < 0:
            t2 = -t2
            n2 = -n2
            rho2 = -rho2

        s_ref = (
            (refined-center2)
            @ t2
        )

        d_ref = (
            refined@n2-rho2
        )

        line_rmse = float(
            np.sqrt(
                np.mean(
                    d_ref**2
                )
            )
        )

        s_span = float(
            np.percentile(
                s_ref,
                97.0,
            )
            - np.percentile(
                s_ref,
                3.0,
            )
        )

        # ------------------------------------------------------
        # Curvature gate: line versus quadratic edge model
        # ------------------------------------------------------
        A1 = np.column_stack([
            np.ones_like(s_ref),
            s_ref,
        ])

        c1, *_ = np.linalg.lstsq(
            A1,
            d_ref,
            rcond=None,
        )

        pred1 = (
            A1@c1
        )

        rmse1 = float(
            np.sqrt(
                np.mean(
                    (
                        d_ref-pred1
                    )**2
                )
            )
        )

        A2 = np.column_stack([
            np.ones_like(s_ref),
            s_ref,
            s_ref**2,
        ])

        c2, *_ = np.linalg.lstsq(
            A2,
            d_ref,
            rcond=None,
        )

        pred2 = (
            A2@c2
        )

        rmse2 = float(
            np.sqrt(
                np.mean(
                    (
                        d_ref-pred2
                    )**2
                )
            )
        )

        s_grid = np.linspace(
            float(np.min(s_ref)),
            float(np.max(s_ref)),
            300,
        )

        line_grid = (
            c1[0]
            + c1[1]*s_grid
        )

        quad_grid = (
            c2[0]
            + c2[1]*s_grid
            + c2[2]*s_grid**2
        )

        curvature_sag = float(
            np.max(
                np.abs(
                    quad_grid-line_grid
                )
            )
        )

        quadratic_improvement = float(
            max(
                0.0,
                1.0
                - rmse2
                / max(
                    rmse1,
                    1e-12,
                )
            )
        )

        # Slant relative to nearest sensor axis.
        line_angle = (
            np.degrees(
                np.arctan2(
                    t2[1],
                    t2[0],
                )
            )
            % 180.0
        )

        edge_slant = float(
            min(
                abs(line_angle-0.0),
                abs(line_angle-90.0),
                abs(line_angle-180.0),
            )
        )

        normal_angle = (
            np.degrees(
                np.arctan2(
                    n2[1],
                    n2[0],
                )
            )
            % 180.0
        )

        # Subpixel phase coverage.
        if abs(t2[1]) >= abs(t2[0]):
            # Mostly vertical edge: x(y)
            y_samples = np.arange(
                int(
                    np.ceil(
                        np.min(
                            refined[:, 1]
                        )
                    )
                ),
                int(
                    np.floor(
                        np.max(
                            refined[:, 1]
                        )
                    )
                )+1,
            )

            nx, ny = (
                n2[0],
                n2[1],
            )

            if abs(nx) > 1e-9:
                x_cross = (
                    rho2
                    - ny*y_samples
                ) / nx

                phases = np.mod(
                    x_cross,
                    1.0,
                )
            else:
                phases = np.array([])
        else:
            # Mostly horizontal edge: y(x)
            x_samples = np.arange(
                int(
                    np.ceil(
                        np.min(
                            refined[:, 0]
                        )
                    )
                ),
                int(
                    np.floor(
                        np.max(
                            refined[:, 0]
                        )
                    )
                )+1,
            )

            nx, ny = (
                n2[0],
                n2[1],
            )

            if abs(ny) > 1e-9:
                y_cross = (
                    rho2
                    - nx*x_samples
                ) / ny

                phases = np.mod(
                    y_cross,
                    1.0,
                )
            else:
                phases = np.array([])

        if len(phases) > 0:
            hist, _ = np.histogram(
                phases,
                bins=np.linspace(
                    0.0,
                    1.0,
                    9,
                ),
            )

            phase_coverage = float(
                np.count_nonzero(hist)
                / 8.0
            )
        else:
            phase_coverage = 0.0

        data.edge_normal_xy = (
            float(n2[0]),
            float(n2[1]),
        )

        data.edge_tangent_xy = (
            float(t2[0]),
            float(t2[1]),
        )

        data.edge_rho_px = (
            float(rho2)
        )

        data.edge_center_xy = (
            float(center2[0]),
            float(center2[1]),
        )

        data.edge_refined_points_xy = (
            refined
        )

        data.edge_line_rmse_px = (
            line_rmse
        )

        data.edge_span_px = (
            s_span
        )

        data.edge_slant_deg = (
            edge_slant
        )

        data.edge_normal_angle_deg = (
            normal_angle
        )

        data.curvature_sag_px = (
            curvature_sag
        )

        data.quadratic_improvement = (
            quadratic_improvement
        )

        data.phase_coverage = (
            phase_coverage
        )

        data.valid_profiles = (
            int(len(refined))
        )

        print("========== HALF-MOON STRAIGHT EDGE ==========")
        print(
            f"Refined edge profiles      : "
            f"{len(refined)}"
        )
        print(
            f"Straight-edge span         : "
            f"{s_span:.2f} px"
        )
        print(
            f"Line-fit RMSE              : "
            f"{line_rmse:.4f} px"
        )
        print(
            f"Curvature sag              : "
            f"{curvature_sag:.4f} px"
        )
        print(
            f"Quadratic improvement      : "
            f"{quadratic_improvement:.4f}"
        )
        print(
            f"Edge line slant            : "
            f"{edge_slant:.3f} deg "
            f"(nearest sensor axis)"
        )
        print(
            f"MTF normal direction       : "
            f"{normal_angle:.2f} deg"
        )
        print(
            f"8-bin subpixel phase cover : "
            f"{100*phase_coverage:.1f}%"
        )
        print(
            "===========================================\n"
        )

    # ==========================================================
    # 5) OVERSAMPLED ESF
    # ==========================================================
    @staticmethod
    def _robust_mean(values):
        v = np.asarray(
            values,
            dtype=float,
        )

        if len(v) == 0:
            return np.nan

        if len(v) < 5:
            return float(
                np.mean(v)
            )

        med = float(
            np.median(v)
        )

        sigma = max(
            MTFPipeline._robust_sigma(v),
            1e-12,
        )

        keep = (
            np.abs(v-med)
            <= 3.5*sigma
        )

        if np.count_nonzero(
            keep
        ) < 2:
            return med

        return float(
            np.mean(
                v[keep]
            )
        )

    def build_esf(
        self,
        data,
        oversampling=8,
        normal_half_width_px=8.0,
        endpoint_trim_fraction=0.16,
        min_count_per_bin=3,
    ):
        """
        Use original pixel values.
        No image resampling is used to build the ESF.

        Every pixel is assigned a signed perpendicular distance to the
        fitted straight edge, providing subpixel edge sampling.
        """
        if (
            data.roi is None
            or data.edge_normal_xy is None
        ):
            raise ValueError(
                "Önce detect_straight_edge() çalıştırılmalı."
            )

        img = np.asarray(
            data.roi,
            dtype=float,
        )

        h, w = img.shape

        n = np.asarray(
            data.edge_normal_xy,
            dtype=float,
        )

        t = np.asarray(
            data.edge_tangent_xy,
            dtype=float,
        )

        rho = float(
            data.edge_rho_px
        )

        center = np.asarray(
            data.edge_center_xy,
            dtype=float,
        )

        refined = np.asarray(
            data.edge_refined_points_xy,
            dtype=float,
        )

        s_ref = (
            (refined-center)
            @ t
        )

        s_lo = float(
            np.percentile(
                s_ref,
                2.0,
            )
        )

        s_hi = float(
            np.percentile(
                s_ref,
                98.0,
            )
        )

        trim = (
            endpoint_trim_fraction
            * (s_hi-s_lo)
        )

        s_lo += trim
        s_hi -= trim

        y, x = np.indices(
            img.shape,
            dtype=float,
        )

        points = np.column_stack([
            x.ravel(),
            y.ravel(),
        ])

        d = (
            points@n-rho
        )

        s = (
            (points-center)
            @ t
        )

        use = (
            (s >= s_lo)
            & (s <= s_hi)
            & (np.abs(d) <= normal_half_width_px)
        )

        dv = d[use]
        iv = img.ravel()[use]

        if len(dv) < 200:
            raise RuntimeError(
                "ESF için yeterli straight-edge pikseli yok."
            )

        # Determine polarity: make negative d = bright side,
        # positive d = dark side.
        neg_far = iv[
            dv <= -0.55*normal_half_width_px
        ]

        pos_far = iv[
            dv >= +0.55*normal_half_width_px
        ]

        if (
            len(neg_far) < 15
            or len(pos_far) < 15
        ):
            raise RuntimeError(
                "ESF bright/dark plateau pikselleri yetersiz."
            )

        neg_level = float(
            np.median(
                neg_far
            )
        )

        pos_level = float(
            np.median(
                pos_far
            )
        )

        if neg_level < pos_level:
            dv = -dv

        step = (
            1.0
            / int(oversampling)
        )

        edges = np.arange(
            -normal_half_width_px,
            normal_half_width_px
            + step*1.0001,
            step,
        )

        centers = (
            0.5
            * (
                edges[:-1]
                + edges[1:]
            )
        )

        ids = (
            np.digitize(
                dv,
                edges,
            )
            - 1
        )

        esf = np.full(
            len(centers),
            np.nan,
            dtype=float,
        )

        counts = np.zeros(
            len(centers),
            dtype=int,
        )

        for k in range(
            len(centers)
        ):
            vals = iv[
                ids == k
            ]

            counts[k] = (
                len(vals)
            )

            if len(vals) >= min_count_per_bin:
                esf[k] = (
                    self._robust_mean(
                        vals
                    )
                )

        good = np.isfinite(
            esf
        )

        if np.count_nonzero(
            good
        ) < 0.70*len(esf):
            raise RuntimeError(
                "Oversampled ESF bin doluluğu yetersiz."
            )

        # Only fill genuinely empty bins, never smooth by interpolation.
        esf[~good] = np.interp(
            centers[~good],
            centers[good],
            esf[good],
        )

        bright_mask = (
            centers
            <= -0.55*normal_half_width_px
        )

        dark_mask = (
            centers
            >= +0.55*normal_half_width_px
        )

        bright_level = float(
            np.median(
                esf[bright_mask]
            )
        )

        dark_level = float(
            np.median(
                esf[dark_mask]
            )
        )

        if bright_level <= dark_level:
            raise RuntimeError(
                "Half-moon ESF polarity/contrast geçersiz."
            )

        # Noise statistics from the actual pixels, not binned ESF.
        bright_pixels = iv[
            dv <= -0.55*normal_half_width_px
        ]

        dark_pixels = iv[
            dv >= +0.55*normal_half_width_px
        ]

        bright_sigma = float(
            self._robust_sigma(
                bright_pixels
            )
        )

        dark_sigma = float(
            self._robust_sigma(
                dark_pixels
            )
        )

        pooled = float(
            np.sqrt(
                0.5
                * (
                    bright_sigma**2
                    + dark_sigma**2
                )
            )
        )

        cnr = float(
            (
                bright_level-dark_level
            )
            / max(
                pooled,
                1e-12,
            )
        )

        esf_norm = (
            (esf-dark_level)
            / (
                bright_level-dark_level
            )
        )

        data.esf_d_px = (
            centers
        )

        data.esf_signal = (
            esf_norm
        )

        data.esf_counts = (
            counts
        )

        data.bright_level_dn = (
            bright_level
        )

        data.dark_level_dn = (
            dark_level
        )

        data.bright_sigma_dn = (
            bright_sigma
        )

        data.dark_sigma_dn = (
            dark_sigma
        )

        data.cnr = (
            cnr
        )

        print("========== OVERSAMPLED ESF ==========")
        print(
            f"Oversampling               : "
            f"{oversampling}x"
        )
        print(
            f"ESF bin step               : "
            f"{step:.4f} px"
        )
        print(
            f"Straight segment used      : "
            f"{s_hi-s_lo:.2f} px"
        )
        print(
            f"Bright plateau             : "
            f"{bright_level:.3f} DN"
        )
        print(
            f"Dark plateau               : "
            f"{dark_level:.3f} DN"
        )
        print(
            f"Bright robust sigma        : "
            f"{bright_sigma:.3f} DN"
        )
        print(
            f"Dark robust sigma          : "
            f"{dark_sigma:.3f} DN"
        )
        print(
            f"CNR                        : "
            f"{cnr:.2f}"
        )
        print(
            f"Filled bins                : "
            f"{np.count_nonzero(counts >= min_count_per_bin)}"
            f"/{len(counts)}"
        )
        print("====================================\n")

    # ==========================================================
    # 6) LSF + MTF
    # ==========================================================
    @staticmethod
    def _first_crossing(
        freq,
        mtf,
        level,
    ):
        f = np.asarray(
            freq,
            dtype=float,
        )

        m = np.asarray(
            mtf,
            dtype=float,
        )

        idx = np.where(
            (m[:-1] >= level)
            & (m[1:] < level)
        )[0]

        if len(idx) == 0:
            return np.nan

        i = int(
            idx[0]
        )

        if m[i+1] == m[i]:
            return float(
                f[i]
            )

        q = (
            (level-m[i])
            / (
                m[i+1]-m[i]
            )
        )

        return float(
            f[i]
            + q*(
                f[i+1]-f[i]
            )
        )

    def calculate_lsf_and_mtf(
        self,
        data,
        taper_alpha=0.12,
    ):
        if (
            data.esf_d_px is None
            or data.esf_signal is None
        ):
            raise ValueError(
                "Önce build_esf() çalıştırılmalı."
            )

        d = np.asarray(
            data.esf_d_px,
            dtype=float,
        )

        esf = np.asarray(
            data.esf_signal,
            dtype=float,
        )

        dx = float(
            np.mean(
                np.diff(d)
            )
        )

        # Adaptive, weak smoothing only when CNR requires it.
        if data.cnr >= 20.0:
            esf_for_derivative = (
                esf.copy()
            )
            smooth_desc = "none (CNR >= 20)"
        elif data.cnr >= 10.0:
            window = 5
            esf_for_derivative = (
                savgol_filter(
                    esf,
                    window_length=window,
                    polyorder=3,
                    mode="interp",
                )
            )
            smooth_desc = "Savitzky-Golay 5 bins"
        else:
            window = 7
            esf_for_derivative = (
                savgol_filter(
                    esf,
                    window_length=window,
                    polyorder=3,
                    mode="interp",
                )
            )
            smooth_desc = "Savitzky-Golay 7 bins"

        # Bright -> dark, so negative derivative is positive LSF.
        lsf = (
            -np.gradient(
                esf_for_derivative,
                dx,
                edge_order=2,
            )
        )

        # Remove tiny derivative baseline from the tails.
        tail_n = max(
            4,
            int(
                round(
                    0.10*len(lsf)
                )
            ),
        )

        baseline = float(
            np.median(
                np.concatenate([
                    lsf[:tail_n],
                    lsf[-tail_n:],
                ])
            )
        )

        lsf = (
            lsf-baseline
        )

        # Small end taper only; central LSF is untouched.
        window = tukey(
            len(lsf),
            alpha=float(taper_alpha),
        )

        lsf_tapered = (
            lsf*window
        )

        area = float(
            np.trapezoid(
                lsf_tapered,
                d,
            )
        )

        if area < 0:
            lsf_tapered = (
                -lsf_tapered
            )
            area = -area

        if area <= 1e-12:
            raise RuntimeError(
                "LSF alanı geçersiz."
            )

        lsf_tapered = (
            lsf_tapered/area
        )

        peak = float(
            np.max(
                np.abs(
                    lsf_tapered
                )
            )
        )

        endpoint = float(
            max(
                np.max(
                    np.abs(
                        lsf_tapered[:tail_n]
                    )
                ),
                np.max(
                    np.abs(
                        lsf_tapered[-tail_n:]
                    )
                ),
            )
        )

        endpoint_ratio = (
            endpoint
            / max(
                peak,
                1e-12,
            )
        )

        data.lsf_d_px = (
            d
        )

        data.lsf_signal = (
            lsf_tapered
        )

        data.lsf_endpoint_ratio = (
            endpoint_ratio
        )

        # ------------------------------------------------------
        # FFT
        # ------------------------------------------------------
        n_fft = 1

        target_len = max(
            16384,
            16*len(lsf_tapered),
        )

        while n_fft < target_len:
            n_fft *= 2

        fft_lsf = np.fft.rfft(
            lsf_tapered,
            n=n_fft,
        )

        freq_cpp = np.fft.rfftfreq(
            n_fft,
            d=dx,
        )

        mtf = np.abs(
            fft_lsf
        )

        mtf = (
            mtf
            / max(
                float(mtf[0]),
                1e-12,
            )
        )

        # Central-difference derivative correction:
        # ideal derivative / numerical derivative
        x = (
            2.0*np.pi
            * freq_cpp
            * dx
        )

        correction = np.ones_like(
            x
        )

        nz = (
            np.abs(x) > 1e-12
        )

        sx = np.sin(
            x[nz]
        )

        good = (
            np.abs(sx) > 1e-8
        )

        tmp = np.ones(
            np.count_nonzero(nz),
            dtype=float,
        )

        tmp[good] = (
            x[nz][good]
            / sx[good]
        )

        correction[nz] = (
            tmp
        )

        # Only a very small correction is needed below sensor Nyquist.
        mtf = (
            mtf*correction
        )

        nyquist_cpp = 0.5

        valid = (
            freq_cpp <= nyquist_cpp
        )

        freq_cpp = (
            freq_cpp[valid]
        )

        mtf = (
            mtf[valid]
        )

        freq_lpmm = (
            freq_cpp
            / float(
                data.pixel_pitch_mm
            )
        )

        nyquist_lpmm = (
            0.5
            / float(
                data.pixel_pitch_mm
            )
        )

        data.mtf_freq_cpp = (
            freq_cpp
        )

        data.mtf_freq_lpmm = (
            freq_lpmm
        )

        data.mtf_signal = (
            mtf
        )

        data.nyquist_lpmm = (
            nyquist_lpmm
        )

        data.mtf_at_10_lpmm = float(
            np.interp(
                10.0,
                freq_lpmm,
                mtf,
            )
        )

        # Sample the already-computed MTF curve at sensor Nyquist.
        # This does NOT change the MTF algorithm.
        data.mtf_at_nyquist = float(
            np.interp(
                nyquist_lpmm,
                freq_lpmm,
                mtf,
            )
        )

        data.mtf50_lpmm = (
            self._first_crossing(
                freq_lpmm,
                mtf,
                0.50,
            )
        )

        data.mtf10_lpmm = (
            self._first_crossing(
                freq_lpmm,
                mtf,
                0.10,
            )
        )

        print("========== LSF / MTF ==========")
        print(
            f"ESF derivative smoothing   : "
            f"{smooth_desc}"
        )
        print(
            f"LSF endpoint / peak        : "
            f"{endpoint_ratio:.4f}"
        )
        print(
            f"Sensor Nyquist             : "
            f"{nyquist_lpmm:.3f} lp/mm"
        )
        print(
            f"MTF @ 10 lp/mm             : "
            f"{100*data.mtf_at_10_lpmm:.2f}%"
        )
        print(
            f"MTF @ Nyquist              : "
            f"{100*data.mtf_at_nyquist:.2f}%"
        )
        print(
            f"MTF50                      : "
            f"{data.mtf50_lpmm:.3f} lp/mm"
        )
        print(
            f"MTF10                      : "
            f"{data.mtf10_lpmm:.3f} lp/mm"
        )
        print(
            f"Measured direction         : "
            f"{data.edge_normal_angle_deg:.2f} deg "
            f"(sensor X-axis reference)"
        )
        print("============================\n")

    # ==========================================================
    # 7) QUALITY GATES
    # ==========================================================
    def evaluate_quality(
        self,
        data,
    ):
        warnings = []

        # Edge straightness
        if data.edge_line_rmse_px > 0.35:
            warnings.append(
                f"edge line RMSE yüksek: "
                f"{data.edge_line_rmse_px:.3f}px"
            )

        if data.curvature_sag_px > 0.30:
            warnings.append(
                f"curvature sag yüksek: "
                f"{data.curvature_sag_px:.3f}px; "
                f"curved arc karışmış olabilir"
            )

        if data.quadratic_improvement > 0.25:
            warnings.append(
                f"quadratic curvature improvement yüksek: "
                f"{data.quadratic_improvement:.3f}"
            )

        # Sampling
        if data.edge_slant_deg < 1.0:
            warnings.append(
                f"edge sensor eksenine fazla paralel: "
                f"{data.edge_slant_deg:.2f}°"
            )
        elif data.edge_slant_deg > 15.0:
            warnings.append(
                f"edge slant yüksek: "
                f"{data.edge_slant_deg:.2f}°; "
                f"ideal yaklaşık 2-10°"
            )

        if data.phase_coverage < 0.75:
            warnings.append(
                f"subpixel phase coverage düşük: "
                f"{100*data.phase_coverage:.1f}%"
            )

        # SNR
        if data.cnr < 5.0:
            warnings.append(
                f"CNR düşük: {data.cnr:.2f}"
            )
        elif data.cnr < 10.0:
            warnings.append(
                f"CNR marjinal: {data.cnr:.2f}"
            )

        if data.valid_profiles < 30:
            warnings.append(
                f"valid profile az: "
                f"{data.valid_profiles}"
            )

        if data.edge_span_px < 35.0:
            warnings.append(
                f"straight edge span kısa: "
                f"{data.edge_span_px:.1f}px"
            )

        if data.lsf_endpoint_ratio > 0.08:
            warnings.append(
                f"LSF tail ROI sonunda hâlâ yüksek: "
                f"{100*data.lsf_endpoint_ratio:.1f}%"
            )

        # Determine severity.
        hard_fail = (
            data.edge_line_rmse_px > 0.55
            or data.curvature_sag_px > 0.60
            or data.quadratic_improvement > 0.50
            or data.cnr < 4.0
            or data.valid_profiles < 20
            or data.phase_coverage < 0.40
        )

        if hard_fail:
            status = "REJECT"
        elif len(warnings) == 0:
            status = "GOOD"
        else:
            status = "MARGINAL"

        data.quality_status = (
            status
        )

        data.quality_warnings = (
            warnings
        )

        print("========== QUALITY ==========")
        print(
            f"Status                     : "
            f"{status}"
        )
        print(
            f"Line RMSE                  : "
            f"{data.edge_line_rmse_px:.4f} px"
        )
        print(
            f"Curvature sag              : "
            f"{data.curvature_sag_px:.4f} px"
        )
        print(
            f"CNR                        : "
            f"{data.cnr:.2f}"
        )
        print(
            f"Valid profiles             : "
            f"{data.valid_profiles}"
        )
        print(
            f"Phase coverage             : "
            f"{100*data.phase_coverage:.1f}%"
        )

        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(
                    f"  - {warning}"
                )

        print("============================\n")

        if status == "REJECT":
            print(
                "NOT: MTF eğrisi diagnostic amaçla üretildi, "
                "ancak kalite gate REJECT verdi.\n"
            )

    # ==========================================================
    # COMPLETE PIPELINE
    # ==========================================================
    def run(
        self,
        data,
    ):
        self.load_mat_image(
            data
        )

        self.subtract_background(
            data
        )

        self.crop_roi(
            data
        )

        self.detect_straight_edge(
            data
        )

        self.build_esf(
            data,
            oversampling=8,
        )

        self.calculate_lsf_and_mtf(
            data
        )

        self.evaluate_quality(
            data
        )

        return (
            data.mtf_freq_lpmm,
            data.mtf_signal,
        )

    # ==========================================================
    # SAME ORIGINAL ALGORITHM FOR PHYSICAL SENSOR X + Y
    # ==========================================================
    @staticmethod
    def _axis_distance_from_normal(angle_deg):
        """
        MTF direction is normal to the straight edge.

        normal ~= 0/180 deg -> sensor X MTF
        normal ~= 90 deg    -> sensor Y MTF
        """
        a = float(angle_deg) % 180.0

        dx = min(
            abs(a),
            abs(a-180.0),
        )

        dy = abs(
            a-90.0
        )

        return (
            float(dx),
            float(dy),
        )

    @staticmethod
    def _snapshot_result(data):
        return {
            "data": data,
            "path": str(data.data_path),
            "normal_deg": float(
                data.edge_normal_angle_deg
            ),
            "mtf_at_10": float(
                data.mtf_at_10_lpmm
            ),
            "mtf_at_nyquist": float(
                data.mtf_at_nyquist
            ),
            "mtf50": float(
                data.mtf50_lpmm
            ),
            "mtf10": float(
                data.mtf10_lpmm
            ),
            "quality": str(
                data.quality_status
            ),
        }

    def run_xy(
        self,
        data_a,
        data_b,
        axis_tolerance_deg=20.0,
    ):
        """
        Run THE SAME original straight-edge pipeline independently
        on two physical half-moon captures.

        One capture must provide an MTF normal close to sensor X.
        The other capture must provide an MTF normal close to sensor Y.

        No image rotation, no curved-arc MTF, no X/Y decomposition.
        """
        print(
            "\n"
            "##################################################\n"
            "               FRAME A ANALYSIS\n"
            "##################################################"
        )

        self.run(
            data_a
        )

        ra = self._snapshot_result(
            data_a
        )

        print(
            "\n"
            "##################################################\n"
            "               FRAME B ANALYSIS\n"
            "##################################################"
        )

        self.run(
            data_b
        )

        rb = self._snapshot_result(
            data_b
        )

        a_x, a_y = (
            self._axis_distance_from_normal(
                ra["normal_deg"]
            )
        )

        b_x, b_y = (
            self._axis_distance_from_normal(
                rb["normal_deg"]
            )
        )

        # Find the physically consistent X/Y assignment.
        cost_ab = (
            a_x+b_y
        )

        cost_ba = (
            b_x+a_y
        )

        if cost_ab <= cost_ba:
            rx = ra
            ry = rb
        else:
            rx = rb
            ry = ra

        x_dx, _ = (
            self._axis_distance_from_normal(
                rx["normal_deg"]
            )
        )

        _, y_dy = (
            self._axis_distance_from_normal(
                ry["normal_deg"]
            )
        )

        if (
            x_dx > axis_tolerance_deg
            or y_dy > axis_tolerance_deg
        ):
            raise RuntimeError(
                "X/Y yönleri ayrı fiziksel ölçümler olarak bulunamadı. "
                f"X adayı normal={rx['normal_deg']:.2f}°, "
                f"Y adayı normal={ry['normal_deg']:.2f}°. "
                "X ölçümü için normal yaklaşık 0/180°, "
                "Y ölçümü için yaklaşık 90° olmalı."
            )

        print(
            "\n"
            "==================================================\n"
            "              FINAL SENSOR X / Y MTF\n"
            "=================================================="
        )

        print(
            f"Sensor Nyquist              : "
            f"{rx['data'].nyquist_lpmm:.3f} lp/mm"
        )
        print(
            "--------------------------------------------------"
        )

        print(
            f"MTF_X source                : "
            f"{rx['path']}"
        )
        print(
            f"MTF_X normal direction      : "
            f"{rx['normal_deg']:.2f} deg"
        )
        print(
            f"MTF_X @ 10 lp/mm            : "
            f"{100*rx['mtf_at_10']:.2f}%"
        )
        print(
            f"MTF_X @ Nyquist             : "
            f"{100*rx['mtf_at_nyquist']:.2f}%"
        )
        print(
            f"MTF50_X                     : "
            f"{rx['mtf50']:.3f} lp/mm"
        )
        print(
            f"MTF10_X                     : "
            f"{rx['mtf10']:.3f} lp/mm"
        )
        print(
            f"MTF_X quality               : "
            f"{rx['quality']}"
        )

        print(
            "--------------------------------------------------"
        )

        print(
            f"MTF_Y source                : "
            f"{ry['path']}"
        )
        print(
            f"MTF_Y normal direction      : "
            f"{ry['normal_deg']:.2f} deg"
        )
        print(
            f"MTF_Y @ 10 lp/mm            : "
            f"{100*ry['mtf_at_10']:.2f}%"
        )
        print(
            f"MTF_Y @ Nyquist             : "
            f"{100*ry['mtf_at_nyquist']:.2f}%"
        )
        print(
            f"MTF50_Y                     : "
            f"{ry['mtf50']:.3f} lp/mm"
        )
        print(
            f"MTF10_Y                     : "
            f"{ry['mtf10']:.3f} lp/mm"
        )
        print(
            f"MTF_Y quality               : "
            f"{ry['quality']}"
        )

        print(
            "==================================================\n"
        )

        return {
            "x": rx,
            "y": ry,
        }


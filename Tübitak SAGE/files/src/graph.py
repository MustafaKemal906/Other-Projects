import numpy as np
import matplotlib.pyplot as plt


class Graph:
    def data_visualization(
        self,
        data,
        title_prefix="",
    ):
        if data.intensity is None:
            raise ValueError(
                "Önce pipeline çalıştırılmalı."
            )

        plt.figure(
            figsize=(9, 7)
        )

        im = plt.imshow(
            data.intensity,
            cmap="viridis",
            interpolation="nearest",
        )

        plt.colorbar(
            im,
            label="DN",
        )

        plt.title(
            f"{title_prefix}MAT Image"
        )

        plt.xlabel(
            "X [pixel]"
        )

        plt.ylabel(
            "Y [pixel]"
        )

        plt.tight_layout()
        plt.show()

    def plot_background_subtracted(
        self,
        data,
        title_prefix="",
    ):
        if data.background_subtracted is None:
            raise ValueError(
                "Background-subtracted image yok."
            )

        plt.figure(
            figsize=(9, 7)
        )

        im = plt.imshow(
            data.background_subtracted,
            cmap="viridis",
            interpolation="nearest",
        )

        plt.colorbar(
            im,
            label="Background-subtracted DN",
        )

        plt.title(
            f"{title_prefix}Background Subtracted"
        )

        plt.xlabel(
            "X [pixel]"
        )

        plt.ylabel(
            "Y [pixel]"
        )

        plt.tight_layout()
        plt.show()

    def plot_roi_edge(
        self,
        data,
        title_prefix="",
    ):
        if data.roi is None:
            raise ValueError(
                "ROI yok."
            )

        plt.figure(
            figsize=(8, 7)
        )

        ax = plt.gca()

        im = ax.imshow(
            data.roi,
            cmap="viridis",
            interpolation="nearest",
        )

        plt.colorbar(
            im,
            ax=ax,
            label="Local-background-corrected DN",
        )

        if (
            data.edge_ransac_inliers_xy
            is not None
        ):
            pts = np.asarray(
                data.edge_ransac_inliers_xy
            )

            ax.scatter(
                pts[:, 0],
                pts[:, 1],
                s=8,
                alpha=0.35,
                label="RANSAC inliers",
            )

        if (
            data.edge_refined_points_xy
            is not None
        ):
            pts = np.asarray(
                data.edge_refined_points_xy
            )

            ax.scatter(
                pts[:, 0],
                pts[:, 1],
                s=18,
                marker="x",
                label="Subpixel edge points",
            )

        if (
            data.edge_normal_xy is not None
            and data.edge_tangent_xy is not None
            and data.edge_center_xy is not None
        ):
            c = np.asarray(
                data.edge_center_xy,
                dtype=float,
            )

            t = np.asarray(
                data.edge_tangent_xy,
                dtype=float,
            )

            s = np.linspace(
                -0.55*data.edge_span_px,
                +0.55*data.edge_span_px,
                200,
            )

            line = (
                c[None, :]
                + s[:, None]*t[None, :]
            )

            ax.plot(
                line[:, 0],
                line[:, 1],
                linewidth=2.2,
                label=(
                    f"Fitted straight edge | "
                    f"normal={data.edge_normal_angle_deg:.2f}°"
                ),
            )

        ax.set_title(
            f"{title_prefix}Half-Moon ROI + Straight Edge\n"
            f"RMSE={data.edge_line_rmse_px:.4f}px | "
            f"slant={data.edge_slant_deg:.2f}° | "
            f"quality={data.quality_status}"
        )

        ax.set_xlabel(
            "ROI X [pixel]"
        )

        ax.set_ylabel(
            "ROI Y [pixel]"
        )

        ax.legend(
            loc="best",
        )

        plt.tight_layout()
        plt.show()

    def plot_edge_residuals(
        self,
        data,
        title_prefix="",
    ):
        pts = np.asarray(
            data.edge_refined_points_xy,
            dtype=float,
        )

        n = np.asarray(
            data.edge_normal_xy,
            dtype=float,
        )

        t = np.asarray(
            data.edge_tangent_xy,
            dtype=float,
        )

        c = np.asarray(
            data.edge_center_xy,
            dtype=float,
        )

        rho = float(
            data.edge_rho_px
        )

        s = (
            (pts-c)@t
        )

        residual = (
            pts@n-rho
        )

        order = np.argsort(
            s
        )

        plt.figure(
            figsize=(9, 5)
        )

        plt.plot(
            s[order],
            residual[order],
            marker="o",
            markersize=3,
            linewidth=1.2,
            label="Subpixel line residual",
        )

        plt.axhline(
            0.0,
            linestyle="--",
        )

        plt.xlabel(
            "Position along straight edge [pixel]"
        )

        plt.ylabel(
            "Normal residual [pixel]"
        )

        plt.title(
            f"{title_prefix}Straight-Edge Residuals\n"
            f"RMSE={data.edge_line_rmse_px:.4f}px | "
            f"curvature sag={data.curvature_sag_px:.4f}px"
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_esf(
        self,
        data,
        title_prefix="",
    ):
        plt.figure(
            figsize=(9, 5.5)
        )

        plt.plot(
            data.esf_d_px,
            data.esf_signal,
            linewidth=2.2,
            label="ESF",
        )

        plt.axvline(
            0.0,
            linestyle="--",
            alpha=0.6,
        )

        plt.axhline(
            0.5,
            linestyle=":",
            alpha=0.6,
        )

        plt.xlabel(
            "Signed distance from straight edge [pixel]"
        )

        plt.ylabel(
            "Normalized intensity"
        )

        plt.title(
            f"{title_prefix}Oversampled ESF\n"
            f"CNR={data.cnr:.1f} | "
            f"phase coverage={100*data.phase_coverage:.0f}%"
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_lsf(
        self,
        data,
        title_prefix="",
    ):
        plt.figure(
            figsize=(9, 5.5)
        )

        plt.plot(
            data.lsf_d_px,
            data.lsf_signal,
            linewidth=2.2,
            label="LSF",
        )

        plt.axvline(
            0.0,
            linestyle="--",
            alpha=0.6,
        )

        plt.xlabel(
            "Signed distance [pixel]"
        )

        plt.ylabel(
            "Normalized LSF"
        )

        plt.title(
            f"{title_prefix}Line Spread Function\n"
            f"endpoint/peak={data.lsf_endpoint_ratio:.4f}"
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_mtf(
        self,
        data,
        axis_name=None,
        title_prefix="",
    ):
        label = (
            axis_name
            if axis_name is not None
            else "MTF"
        )

        plt.figure(
            figsize=(10, 6)
        )

        plt.plot(
            data.mtf_freq_lpmm,
            data.mtf_signal,
            linewidth=2.5,
            label=(
                f"{label} | "
                f"@10={100*data.mtf_at_10_lpmm:.2f}% | "
                f"@Nyq={100*data.mtf_at_nyquist:.2f}%"
            ),
        )

        plt.axvline(
            10.0,
            linestyle=":",
            label="10 lp/mm",
        )

        plt.axvline(
            data.nyquist_lpmm,
            linestyle="--",
            alpha=0.65,
            label=(
                f"Nyquist "
                f"{data.nyquist_lpmm:.3f} lp/mm"
            ),
        )

        plt.axhline(
            0.5,
            linestyle="--",
            alpha=0.5,
            label="MTF50",
        )

        plt.axhline(
            0.1,
            linestyle=":",
            alpha=0.5,
            label="MTF10",
        )

        plt.xlim(
            0,
            data.nyquist_lpmm,
        )

        plt.ylim(
            0,
            1.05,
        )

        plt.xlabel(
            "Spatial frequency [lp/mm]"
        )

        plt.ylabel(
            "MTF"
        )

        plt.title(
            f"{title_prefix}{label} — Straight-Edge MTF"
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.legend(
            loc="best",
        )

        plt.tight_layout()
        plt.show()

    def plot_xy_comparison(
        self,
        x_data,
        y_data,
    ):
        plt.figure(
            figsize=(10, 6)
        )

        plt.plot(
            x_data.mtf_freq_lpmm,
            x_data.mtf_signal,
            linewidth=2.5,
            label=(
                f"MTF_X | @10="
                f"{100*x_data.mtf_at_10_lpmm:.2f}% | "
                f"@Nyq="
                f"{100*x_data.mtf_at_nyquist:.2f}%"
            ),
        )

        plt.plot(
            y_data.mtf_freq_lpmm,
            y_data.mtf_signal,
            linewidth=2.5,
            label=(
                f"MTF_Y | @10="
                f"{100*y_data.mtf_at_10_lpmm:.2f}% | "
                f"@Nyq="
                f"{100*y_data.mtf_at_nyquist:.2f}%"
            ),
        )

        plt.axvline(
            10.0,
            linestyle=":",
            label="10 lp/mm",
        )

        plt.axvline(
            x_data.nyquist_lpmm,
            linestyle="--",
            alpha=0.65,
            label=(
                f"Nyquist "
                f"{x_data.nyquist_lpmm:.3f} lp/mm"
            ),
        )

        plt.axhline(
            0.5,
            linestyle="--",
            alpha=0.45,
        )

        plt.axhline(
            0.1,
            linestyle=":",
            alpha=0.45,
        )

        plt.xlim(
            0,
            x_data.nyquist_lpmm,
        )

        plt.ylim(
            0,
            1.05,
        )

        plt.xlabel(
            "Spatial frequency [lp/mm]"
        )

        plt.ylabel(
            "MTF"
        )

        plt.title(
            "Sensor MTF_X vs MTF_Y — Same Straight-Edge Algorithm"
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.legend(
            loc="best",
        )

        plt.tight_layout()
        plt.show()

    def plot_xy_summary_bar(
        self,
        x_data,
        y_data,
    ):
        labels = [
            "10 lp/mm",
            "Nyquist",
        ]

        x_values = [
            100*x_data.mtf_at_10_lpmm,
            100*x_data.mtf_at_nyquist,
        ]

        y_values = [
            100*y_data.mtf_at_10_lpmm,
            100*y_data.mtf_at_nyquist,
        ]

        idx = np.arange(
            len(labels)
        )

        width = 0.36

        plt.figure(
            figsize=(8.5, 5.5)
        )

        plt.bar(
            idx-width/2,
            x_values,
            width,
            label="MTF_X",
        )

        plt.bar(
            idx+width/2,
            y_values,
            width,
            label="MTF_Y",
        )

        plt.xticks(
            idx,
            labels,
        )

        plt.ylabel(
            "MTF [%]"
        )

        plt.title(
            "Directional MTF Summary"
        )

        plt.grid(
            True,
            axis="y",
            alpha=0.3,
        )

        plt.legend()
        plt.tight_layout()
        plt.show()

    def show_all_for_axis(
        self,
        data,
        axis_name,
    ):
        prefix = (
            f"{axis_name} | "
        )

        self.data_visualization(
            data,
            title_prefix=prefix,
        )

        self.plot_background_subtracted(
            data,
            title_prefix=prefix,
        )

        self.plot_roi_edge(
            data,
            title_prefix=prefix,
        )

        self.plot_edge_residuals(
            data,
            title_prefix=prefix,
        )

        self.plot_esf(
            data,
            title_prefix=prefix,
        )

        self.plot_lsf(
            data,
            title_prefix=prefix,
        )

        self.plot_mtf(
            data,
            axis_name=axis_name,
            title_prefix="",
        )

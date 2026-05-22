# -*- coding: utf-8 -*-
from osgeo import gdal
import numpy as np
from scipy.stats import f
import os
import re
import sys
import csv
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


@dataclass
class RasterMeta:
    """Basic metadata for a single-band raster."""

    geotransform: tuple
    projection: str
    x_size: int
    y_size: int
    nodata: Optional[float]


@dataclass
class GeoDetectorStats:
    """GeoDetector statistics for a factor or factor combination."""

    q: float
    vr: float
    p: float
    n: int
    k: int
    ssw: float
    ssb: float
    sst: float
    min_group_size: int
    max_group_size: int


@dataclass
class CandidateResult:
    """Statistics and decision information for one candidate factor."""

    step: int
    candidate_factor: str
    combination: str
    q: float
    delta_q: float
    vr: float
    vr_ratio: float
    s: Optional[float]
    p: float
    n: int
    k: int
    min_group_size: int
    max_group_size: int
    accepted: bool
    reason: str
    raster_path: str


def read_raster(raster_path: str) -> Tuple[np.ndarray, RasterMeta]:
    """Read a single-band raster and return the raster array and metadata."""
    ds = gdal.Open(raster_path)
    if ds is None:
        raise FileNotFoundError(f"Cannot open raster file: {raster_path}")

    band = ds.GetRasterBand(1)
    data = band.ReadAsArray()
    nodata = band.GetNoDataValue()

    meta = RasterMeta(
        geotransform=ds.GetGeoTransform(),
        projection=ds.GetProjection(),
        x_size=ds.RasterXSize,
        y_size=ds.RasterYSize,
        nodata=nodata,
    )

    try:
        stats = band.GetStatistics(True, True)
        print(
            f"[Read] {os.path.basename(raster_path)}: "
            f"min={stats[0]:.6g}, max={stats[1]:.6g}, "
            f"mean={stats[2]:.6g}, std={stats[3]:.6g}, nodata={nodata}"
        )
    except Exception:
        print(f"[Read] {os.path.basename(raster_path)}: nodata={nodata}")

    ds = None
    return data, meta


def is_valid_array(
    arr: np.ndarray,
    nodata: Optional[float],
    treat_zero_as_nodata: bool = False,
) -> np.ndarray:
    """Create a valid-cell mask for a raster array."""
    mask = np.isfinite(arr)

    if nodata is not None:
        if np.isnan(nodata):
            mask &= ~np.isnan(arr)
        else:
            mask &= arr != nodata

    if treat_zero_as_nodata:
        mask &= arr != 0

    return mask


def write_raster(output_path: str, data: np.ndarray, meta: RasterMeta, nodata: int = 0) -> None:
    """Write an Int32 GeoTIFF raster."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(
        output_path,
        meta.x_size,
        meta.y_size,
        1,
        gdal.GDT_Int32,
        options=["COMPRESS=LZW", "TILED=YES"],
    )
    if ds is None:
        raise RuntimeError(f"Cannot create output raster: {output_path}")

    ds.SetGeoTransform(meta.geotransform)
    ds.SetProjection(meta.projection)
    band = ds.GetRasterBand(1)
    band.WriteArray(data.astype(np.int32))
    band.SetNoDataValue(nodata)
    band.FlushCache()
    ds = None


def check_same_grid(
    meta1: RasterMeta,
    meta2: RasterMeta,
    name1: str = "raster1",
    name2: str = "raster2",
) -> None:
    """Check whether two rasters have the same row and column dimensions."""
    if meta1.x_size != meta2.x_size or meta1.y_size != meta2.y_size:
        raise ValueError(
            f"{name1} and {name2} do not have the same raster size: "
            f"{meta1.x_size}x{meta1.y_size} vs {meta2.x_size}x{meta2.y_size}"
        )


def relabel_intersection(raster1_path: str, raster2_path: str, output_path: str) -> str:
    """
    Intersect two categorical rasters and relabel the combined strata.

    A cell is considered valid only when both rasters are valid and non-zero.
    The output raster uses 0 as NoData/invalid cells, and valid interaction
    strata are relabeled from 1 to k.
    """
    data1, meta1 = read_raster(raster1_path)
    data2, meta2 = read_raster(raster2_path)
    check_same_grid(meta1, meta2, raster1_path, raster2_path)

    valid1 = is_valid_array(data1, meta1.nodata, treat_zero_as_nodata=True)
    valid2 = is_valid_array(data2, meta2.nodata, treat_zero_as_nodata=True)
    valid = valid1 & valid2

    out = np.zeros(data1.shape, dtype=np.int32)
    if not np.any(valid):
        raise ValueError(f"The two rasters have no common valid cells: {raster1_path}, {raster2_path}")

    pairs = np.column_stack((data1[valid].ravel(), data2[valid].ravel()))
    _, inverse = np.unique(pairs, axis=0, return_inverse=True)
    out[valid] = inverse.astype(np.int32) + 1

    write_raster(output_path, out, meta1, nodata=0)
    print(f"[Interaction strata] Output raster: {output_path}")
    return output_path


def calculate_geodetector_stats(
    value_raster_path: str,
    label_raster_path: str,
    min_group_size: int = 1,
) -> GeoDetectorStats:
    """
    Calculate q, VR/F statistic, p-value, sample size, and number of strata.

    q = 1 - SSW / SST

    VR = (SSB / (k - 1)) / (SSW / (n - k))

    where:
    - SST is the total sum of squares of the dependent variable.
    - SSW is the within-strata sum of squares.
    - SSB is the between-strata sum of squares.
    - n is the number of valid samples.
    - k is the number of valid strata.
    """
    y_data, y_meta = read_raster(value_raster_path)
    label_data, label_meta = read_raster(label_raster_path)
    check_same_grid(y_meta, label_meta, value_raster_path, label_raster_path)

    valid_y = is_valid_array(y_data, y_meta.nodata, treat_zero_as_nodata=False)
    valid_label = is_valid_array(label_data, label_meta.nodata, treat_zero_as_nodata=True)
    valid = valid_y & valid_label

    y = y_data[valid].astype(float).ravel()
    labels = label_data[valid].ravel()

    if y.size == 0:
        raise ValueError(f"No valid samples are available for calculation: {label_raster_path}")

    unique_labels, inverse, counts = np.unique(labels, return_inverse=True, return_counts=True)

    # Single-sample strata are not removed in the current version.
    # This is done to preserve the original interaction strata generated
    # by raster intersection. The min_group_size argument is retained for
    # interface compatibility and reporting only.
    n = int(y.size)
    k = int(unique_labels.size)

    if k < 2:
        raise ValueError(f"The number of valid strata is less than 2: {label_raster_path}")
    if n <= k:
        raise ValueError(f"Cannot calculate VR/F because n <= k: n={n}, k={k}, file={label_raster_path}")

    overall_mean = float(np.mean(y))
    sst = float(np.sum((y - overall_mean) ** 2))
    if sst <= 0:
        raise ValueError(f"The total variance of the dependent variable is zero: {value_raster_path}")

    sums = np.bincount(inverse, weights=y)
    means = sums / counts
    ssw = float(np.sum((y - means[inverse]) ** 2))
    ssb = max(float(sst - ssw), 0.0)

    q = 1.0 - ssw / sst

    if ssw <= 0:
        vr = float("inf")
        p_value = 0.0
    else:
        vr = (ssb / (k - 1)) / (ssw / (n - k))
        p_value = float(f.sf(vr, k - 1, n - k))

    return GeoDetectorStats(
        q=float(q),
        vr=float(vr),
        p=float(p_value),
        n=n,
        k=k,
        ssw=ssw,
        ssb=ssb,
        sst=sst,
        min_group_size=int(np.min(counts)),
        max_group_size=int(np.max(counts)),
    )


def safe_s_score(q_prev: float, vr_prev: float, q_new: float, vr_new: float, lam: float) -> Tuple[float, float, float]:
    """Calculate Delta q, VR ratio, and S statistic."""
    delta_q = q_new - q_prev

    if vr_prev <= 0 or vr_new <= 0 or not np.isfinite(vr_prev) or not np.isfinite(vr_new):
        vr_ratio = float("nan")
        s_value = float("-inf")
    else:
        vr_ratio = vr_new / vr_prev
        s_value = delta_q - lam * math.log(vr_ratio)

    return float(delta_q), float(vr_ratio), float(s_value)


def factor_name(path: str) -> str:
    """Return the file name without extension as the factor name."""
    return os.path.splitext(os.path.basename(path))[0]


def evaluate_single_factors(
    factor_paths: List[str],
    value_path: str,
    min_group_size: int,
) -> List[CandidateResult]:
    """Step 1: evaluate all single factors using q, VR/F, and p-value."""
    results = []

    for fp in factor_paths:
        stats = calculate_geodetector_stats(value_path, fp, min_group_size=min_group_size)
        results.append(
            CandidateResult(
                step=1,
                candidate_factor=factor_name(fp),
                combination=factor_name(fp),
                q=stats.q,
                delta_q=float("nan"),
                vr=stats.vr,
                vr_ratio=float("nan"),
                s=None,
                p=stats.p,
                n=stats.n,
                k=stats.k,
                min_group_size=stats.min_group_size,
                max_group_size=stats.max_group_size,
                accepted=False,
                reason="single_factor_screening",
                raster_path=fp,
            )
        )

    return results


def choose_initial_factor(single_results: List[CandidateResult], p_threshold: float) -> CandidateResult:
    """
    Select the initial factor.

    The default rule is:
    1. Among statistically significant factors, select the factor with the
       maximum q statistic.
    2. If no factor is significant, still select the maximum-q factor and
       record this situation in the reason field.
    """
    significant = [r for r in single_results if r.p <= p_threshold]
    pool = significant if significant else single_results

    best = max(pool, key=lambda r: r.q)
    best.accepted = True
    best.reason = "initial_selected_by_max_q" if significant else "initial_selected_by_max_q_no_significant_factor"

    return best


def evaluate_step_candidates(
    step: int,
    current_raster: str,
    remaining_factors: List[str],
    value_path: str,
    output_folder: str,
    current_q: float,
    current_vr: float,
    current_combo_names: List[str],
    lam: float,
    p_threshold: float,
    min_group_size: int,
) -> List[CandidateResult]:
    """Evaluate all remaining candidate factors at a given step."""
    results = []
    current_combo_label = "_".join(current_combo_names)

    for fp in remaining_factors:
        cand_name = factor_name(fp)
        out_name = f"step{step}_{current_combo_label}__INTERSECT__{cand_name}.tif"
        out_path = os.path.join(output_folder, out_name)

        relabel_intersection(current_raster, fp, out_path)
        stats = calculate_geodetector_stats(value_path, out_path, min_group_size=min_group_size)
        delta_q, vr_ratio, s_value = safe_s_score(current_q, current_vr, stats.q, stats.vr, lam)

        accepted = False
        if delta_q <= 0:
            reason = "candidate_delta_q_not_positive"
        elif stats.p > p_threshold:
            reason = "candidate_p_not_significant"
        elif s_value <= 0:
            reason = "candidate_S_not_positive"
        else:
            reason = "candidate_passes_filters_but_selection_is_by_max_q"

        results.append(
            CandidateResult(
                step=step,
                candidate_factor=cand_name,
                combination=" ∩ ".join(current_combo_names + [cand_name]),
                q=stats.q,
                delta_q=delta_q,
                vr=stats.vr,
                vr_ratio=vr_ratio,
                s=s_value,
                p=stats.p,
                n=stats.n,
                k=stats.k,
                min_group_size=stats.min_group_size,
                max_group_size=stats.max_group_size,
                accepted=accepted,
                reason=reason,
                raster_path=out_path,
            )
        )

    return results


def write_candidate_csv(path: str, rows: List[CandidateResult]) -> None:
    """Write candidate results to a CSV file."""
    if not rows:
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())

    with open(path, "w", newline="", encoding="utf-8-sig") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for r in rows:
            d = asdict(r)
            if d["s"] is None:
                d["s"] = ""
            writer.writerow(d)


def write_summary_txt(
    path: str,
    selected_path: List[CandidateResult],
    all_candidates: List[CandidateResult],
    lam: float,
    p_threshold: float,
    min_group_size: int,
) -> None:
    """Write a human-readable text report."""
    with open(path, "w", encoding="utf-8") as f_out:
        f_out.write("Stepwise GeoDetector results\n")
        f_out.write("=" * 80 + "\n")
        f_out.write(f"lambda = {lam}\n")
        f_out.write(f"p_threshold = {p_threshold}\n")
        f_out.write(
            f"min_group_size = {min_group_size} "
            "(single-sample strata are not removed in the current version)\n\n"
        )

        f_out.write("[Selected path]\n")
        for r in selected_path:
            s_text = "" if r.s is None else f"{r.s:.6f}"
            dq_text = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            vr_ratio_text = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"

            f_out.write(
                f"Step {r.step}: {r.combination}\n"
                f"  added factor: {r.candidate_factor}\n"
                f"  q={r.q:.6f}, Delta_q={dq_text}, VR={r.vr:.6f}, "
                f"VR_ratio={vr_ratio_text}, S={s_text}, p={r.p:.6g}, "
                f"n={r.n}, k={r.k}, min_group_size={r.min_group_size}, "
                f"max_group_size={r.max_group_size}\n"
                f"  raster: {r.raster_path}\n"
                f"  reason: {r.reason}\n\n"
            )

        f_out.write("\n[All candidate results]\n")
        for r in all_candidates:
            s_text = "" if r.s is None else f"{r.s:.6f}"
            dq_text = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            vr_ratio_text = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"

            f_out.write(
                f"Step {r.step} | {r.combination} | q={r.q:.6f}, "
                f"Delta_q={dq_text}, VR={r.vr:.6f}, "
                f"VR_ratio={vr_ratio_text}, S={s_text}, p={r.p:.6g}, "
                f"k={r.k}, min_n={r.min_group_size}, "
                f"accepted={r.accepted}, reason={r.reason}\n"
            )


def strip_inline_comment(line: str) -> str:
    """
    Remove inline comments beginning with #.

    This allows entries such as:
        PGA.tif  # peak ground acceleration classes

    to be read correctly as:
        PGA.tif
    """
    return line.split("#", 1)[0].strip()


def read_input_file(txt_path: str) -> Dict:
    """
    Read the input configuration file.

    Supported English keys:
    - input_folder, workspace
    - value_file, y, dependent
    - output_folder, output
    - factor_files, factors
    - lambda, lam
    - p_threshold, pvalue, p_value
    - min_group_size, min_n

    Some Chinese keys from older versions are also supported for compatibility.
    """
    config = {
        "input_folder": "",
        "value_file": "",
        "factor_files": [],
        "output_folder": "stepwise_output",
        "lambda": 1.0,
        "p_threshold": 0.05,
        "min_group_size": 1,
    }

    with open(txt_path, "r", encoding="utf-8") as f_in:
        raw_lines = []
        for line in f_in:
            clean = strip_inline_comment(line)
            if clean:
                raw_lines.append(clean)

    in_factor_block = False

    for line in raw_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            in_factor_block = False

            if key in ["input_folder", "workspace"]:
                config["input_folder"] = value
            elif key in ["value_file", "y", "dependent", "dependent_variable"]:
                config["value_file"] = value
            elif key in ["output_folder", "output"]:
                config["output_folder"] = value
            elif key in ["lambda", "λ", "lam", "lambda_value"]:
                config["lambda"] = float(value)
            elif key in ["p_threshold_value", "p_threshold", "pvalue", "p_value"]:
                config["p_threshold"] = float(value)
            elif key in ["minimum_group_size", "min_group_size", "min_n"]:
                config["min_group_size"] = int(value)
            elif key in ["factor_files", "factors", "candidate_factors"]:
                in_factor_block = True
                if value:
                    config["factor_files"].append(value)
            else:
                # For compatibility, an unrecognized key-value line is treated
                # as a factor file entry only when it looks like a raster file.
                if value.lower().endswith((".tif", ".tiff", ".img", ".asc")):
                    config["factor_files"].append(value)
        else:
            # Lines without ":" are treated as factor file names.
            # This is mainly used below the "factor_files:" header.
            if in_factor_block or line.lower().endswith((".tif", ".tiff", ".img", ".asc")):
                config["factor_files"].append(line)

    if not config["input_folder"]:
        config["input_folder"] = os.path.dirname(os.path.abspath(txt_path))

    if not config["value_file"]:
        raise ValueError("The input configuration file does not define value_file.")

    if not config["factor_files"]:
        raise ValueError("The input configuration file does not define factor_files.")

    return config


def is_absolute_path(path: str) -> bool:
    """Return True for Unix, Windows drive-letter, or UNC absolute paths."""
    if not path:
        return False
    return bool(
        os.path.isabs(path)
        or re.match(r"^[A-Za-z]:[\\/]", path)
        or path.startswith("\\\\")
    )


def resolve_path(base_folder: str, file_name: str) -> str:
    """Resolve a path against base_folder when it is not absolute."""
    if is_absolute_path(file_name):
        return os.path.normpath(file_name)
    return os.path.normpath(os.path.join(base_folder, file_name))


def stepwise_geodetector(txt_path: str) -> None:
    """Run the full stepwise GeoDetector workflow."""
    txt_path = os.path.abspath(txt_path)
    config_dir = os.path.dirname(txt_path)
    cfg = read_input_file(txt_path)

    # Relative input_folder values are resolved relative to the folder
    # containing this configuration file, not relative to the current terminal.
    input_folder = resolve_path(config_dir, cfg["input_folder"])
    value_path = resolve_path(input_folder, cfg["value_file"])
    factor_paths = [resolve_path(input_folder, f) for f in cfg["factor_files"]]
    out_folder = resolve_path(input_folder, cfg["output_folder"])
    lam = float(cfg["lambda"])
    p_threshold = float(cfg["p_threshold"])
    min_group_size = int(cfg["min_group_size"])

    os.makedirs(out_folder, exist_ok=True)

    print("\n========== Stepwise GeoDetector ==========")
    print(f"Input folder: {input_folder}")
    print(f"Dependent variable raster: {value_path}")
    print(f"Output folder: {out_folder}")
    print(f"Lambda: {lam}")
    print(f"P-value threshold: {p_threshold}")
    print(
        f"Minimum group size parameter: {min_group_size} "
        "(single-sample strata are not removed in the current version)"
    )
    print("Candidate factor rasters:")
    for fp in factor_paths:
        print(f"  - {fp}")

    all_candidates: List[CandidateResult] = []
    selected_path: List[CandidateResult] = []

    # Step 1: single-factor screening.
    single_results = evaluate_single_factors(factor_paths, value_path, min_group_size=min_group_size)
    all_candidates.extend(single_results)

    initial = choose_initial_factor(single_results, p_threshold=p_threshold)
    selected_path.append(initial)

    print("\n[Step 1] Initial factor selection")
    print(
        f"Selected factor: {initial.candidate_factor}, "
        f"q={initial.q:.6f}, VR={initial.vr:.6f}, p={initial.p:.6g}, k={initial.k}"
    )

    remaining = [fp for fp in factor_paths if factor_name(fp) != initial.candidate_factor]
    current_raster = initial.raster_path
    current_q = initial.q
    current_vr = initial.vr
    current_combo_names = [initial.candidate_factor]

    # Step 2 and later: stepwise interaction evaluation.
    step = 2
    while remaining:
        print(f"\n[Step {step}] Evaluating remaining candidate factors")
        step_results = evaluate_step_candidates(
            step=step,
            current_raster=current_raster,
            remaining_factors=remaining,
            value_path=value_path,
            output_folder=out_folder,
            current_q=current_q,
            current_vr=current_vr,
            current_combo_names=current_combo_names,
            lam=lam,
            p_threshold=p_threshold,
            min_group_size=min_group_size,
        )
        all_candidates.extend(step_results)

        # Selection rule:
        # 1. Keep candidates with Delta q > 0 and p <= threshold.
        # 2. Select the maximum-q candidate from this pool.
        # 3. Use S > 0 to decide whether this maximum-q candidate is retained.
        q_pool = [r for r in step_results if (r.delta_q > 0 and r.p <= p_threshold)]
        if not q_pool:
            print(
                f"[Stop] Step {step}: no candidate satisfies "
                f"Delta q > 0 and p <= {p_threshold}."
            )
            break

        best = max(q_pool, key=lambda r: r.q)

        if best.s is None or best.s <= 0:
            best.accepted = False
            best.reason = "max_q_candidate_rejected_by_S"
            print(
                f"[Stop] Step {step}: the maximum-q candidate is {best.candidate_factor}. "
                f"q={best.q:.6f}, Delta_q={best.delta_q:.6f}, VR={best.vr:.6f}, "
                f"VR_ratio={best.vr_ratio:.6f}, S={best.s:.6f}, p={best.p:.6g}. "
                "Because S <= 0, no new factor is retained."
            )
            break

        best.accepted = True
        best.reason = "selected_by_max_q_retained_by_positive_S"

        for r in step_results:
            if r is not best and r.reason == "candidate_passes_filters_but_selection_is_by_max_q":
                r.reason = "not_selected_because_q_is_lower_than_selected_candidate"

        selected_path.append(best)

        print(
            f"Selected factor: {best.candidate_factor}, q={best.q:.6f}, "
            f"Delta_q={best.delta_q:.6f}, VR={best.vr:.6f}, "
            f"VR_ratio={best.vr_ratio:.6f}, S={best.s:.6f}, p={best.p:.6g}, k={best.k}"
        )

        current_raster = best.raster_path
        current_q = best.q
        current_vr = best.vr
        current_combo_names.append(best.candidate_factor)
        remaining = [fp for fp in remaining if factor_name(fp) != best.candidate_factor]
        step += 1

    # Write output files.
    candidate_csv = os.path.join(out_folder, "all_candidate_results.csv")
    selected_csv = os.path.join(out_folder, "selected_path.csv")
    summary_txt = os.path.join(out_folder, "result.txt")

    write_candidate_csv(candidate_csv, all_candidates)
    write_candidate_csv(selected_csv, selected_path)
    write_summary_txt(summary_txt, selected_path, all_candidates, lam, p_threshold, min_group_size)

    print("\n========== Finished ==========")
    print(f"All candidate results: {candidate_csv}")
    print(f"Selected factor path: {selected_csv}")
    print(f"Text report: {summary_txt}")
    print("Final selected combination:", " ∩ ".join([r.candidate_factor for r in selected_path]))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        txt_path = sys.argv[1]
    else:
        # Use input.txt located in the same folder as this script by default.
        txt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input.txt")

    stepwise_geodetector(txt_path)

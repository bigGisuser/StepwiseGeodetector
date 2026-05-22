# -*- coding: utf-8 -*-

from osgeo import gdal
import numpy as np
from scipy.stats import f
import os
import sys
import csv
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


@dataclass
class RasterMeta:
    geotransform: tuple
    projection: str
    x_size: int
    y_size: int
    nodata: Optional[float]


@dataclass
class GeoDetectorStats:
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
    """读取单波段栅格。"""
    ds = gdal.Open(raster_path)
    if ds is None:
        raise FileNotFoundError(f"无法打开栅格文件: {raster_path}")

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
            f"[读取] {os.path.basename(raster_path)}: "
            f"min={stats[0]:.6g}, max={stats[1]:.6g}, mean={stats[2]:.6g}, std={stats[3]:.6g}, nodata={nodata}"
        )
    except Exception:
        print(f"[读取] {os.path.basename(raster_path)}: nodata={nodata}")

    ds = None
    return data, meta


def is_valid_array(arr: np.ndarray, nodata: Optional[float], treat_zero_as_nodata: bool = False) -> np.ndarray:
    """生成有效像元掩膜。"""
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
    """写出 Int32 GeoTIFF。"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
        raise RuntimeError(f"无法创建输出栅格: {output_path}")

    ds.SetGeoTransform(meta.geotransform)
    ds.SetProjection(meta.projection)
    band = ds.GetRasterBand(1)
    band.WriteArray(data.astype(np.int32))
    band.SetNoDataValue(nodata)
    band.FlushCache()
    ds = None


def check_same_grid(meta1: RasterMeta, meta2: RasterMeta, name1: str = "raster1", name2: str = "raster2") -> None:
    """检查两个栅格尺寸是否一致。"""
    if meta1.x_size != meta2.x_size or meta1.y_size != meta2.y_size:
        raise ValueError(f"{name1} 与 {name2} 尺寸不一致: "
                         f"{meta1.x_size}x{meta1.y_size} vs {meta2.x_size}x{meta2.y_size}")


def relabel_intersection(raster1_path: str, raster2_path: str, output_path: str) -> str:
    """
    两个分类/标签栅格求交互分层。
    有效像元为两个栅格均非 NoData 且非 0 的位置；输出 NoData=0，有效类别从 1 开始。
    """
    data1, meta1 = read_raster(raster1_path)
    data2, meta2 = read_raster(raster2_path)
    check_same_grid(meta1, meta2, raster1_path, raster2_path)

    valid1 = is_valid_array(data1, meta1.nodata, treat_zero_as_nodata=True)
    valid2 = is_valid_array(data2, meta2.nodata, treat_zero_as_nodata=True)
    valid = valid1 & valid2

    out = np.zeros(data1.shape, dtype=np.int32)
    if not np.any(valid):
        raise ValueError(f"两个栅格没有共同有效像元: {raster1_path}, {raster2_path}")

    pairs = np.column_stack((data1[valid].ravel(), data2[valid].ravel()))
    _, inverse = np.unique(pairs, axis=0, return_inverse=True)
    out[valid] = inverse.astype(np.int32) + 1

    write_raster(output_path, out, meta1, nodata=0)
    print(f"[交互分层] 输出: {output_path}")
    return output_path


def calculate_geodetector_stats(value_raster_path: str, label_raster_path: str, min_group_size: int = 1) -> GeoDetectorStats:
    """
    计算 q、VR(F)、p、样本量与分层数量。
    q = 1 - SSW / SST
    VR = (SSB/(k-1)) / (SSW/(n-k))
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
        raise ValueError(f"没有有效样本用于计算: {label_raster_path}")

    unique_labels, inverse, counts = np.unique(labels, return_inverse=True, return_counts=True)

    # 不剔除单样本分层：
    # 为了与原始 GeoDetector 交互计算保持一致，这里保留所有有效分层。
    # min_group_size 参数仅保留在输出和接口中，不再用于过滤分层。
    # 注意：如果交互后分层过细，可能出现 n <= k，此时 VR/F 的自由度无效，代码会提示无法计算。

    n = int(y.size)
    k = int(unique_labels.size)

    if k < 2:
        raise ValueError(f"有效分层数 k < 2，无法计算 GeoDetector: {label_raster_path}")
    if n <= k:
        raise ValueError(f"有效样本数 n <= k，无法计算 VR/F: n={n}, k={k}, file={label_raster_path}")

    overall_mean = float(np.mean(y))
    sst = float(np.sum((y - overall_mean) ** 2))
    if sst <= 0:
        raise ValueError(f"因变量总方差为 0，无法计算 q: {value_raster_path}")

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
    """计算 Δq、VR ratio 和 S。"""
    delta_q = q_new - q_prev
    if vr_prev <= 0 or vr_new <= 0 or not np.isfinite(vr_prev) or not np.isfinite(vr_new):
        # 极端情况下避免 log 出错。通常 VR 应为正。
        vr_ratio = float("nan")
        s_value = float("-inf")
    else:
        vr_ratio = vr_new / vr_prev
        s_value = delta_q - lam * math.log(vr_ratio)
    return float(delta_q), float(vr_ratio), float(s_value)


def factor_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def evaluate_single_factors(factor_paths: List[str], value_path: str, min_group_size: int) -> List[CandidateResult]:
    """Step 1：单因子筛选，只计算 q、VR、p，不计算 S。"""
    results = []
    for fp in factor_paths:
        stats = calculate_geodetector_stats(value_path, fp, min_group_size=min_group_size)
        results.append(CandidateResult(
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
        ))
    return results


def choose_initial_factor(single_results: List[CandidateResult], p_threshold: float) -> CandidateResult:
    """
    初始因子选择：
    优先在 p <= p_threshold 的因子中选择 q 最大者；
    如果没有显著因子，则选择 q 最大者，但在 reason 中标记。
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
    """Step k：计算所有剩余候选因子的 q、VR、p、Δq 和 S。"""
    results = []
    current_combo_label = "_".join(current_combo_names)

    for fp in remaining_factors:
        cand_name = factor_name(fp)
        out_name = f"step{step}_{current_combo_label}__INTERSECT__{cand_name}.tif"
        out_path = os.path.join(output_folder, out_name)

        relabel_intersection(current_raster, fp, out_path)
        stats = calculate_geodetector_stats(value_path, out_path, min_group_size=min_group_size)
        delta_q, vr_ratio, s_value = safe_s_score(current_q, current_vr, stats.q, stats.vr, lam)

        # 注意：这里不直接决定最终保留哪个因子。
        # 方法逻辑为：先按 q 最大选择候选组合，S 只用于判断该 q 最大组合是否保留。
        accepted = False
        if delta_q <= 0:
            reason = "candidate_delta_q_not_positive"
        elif stats.p > p_threshold:
            reason = "candidate_p_not_significant"
        elif s_value <= 0:
            reason = "candidate_S_not_positive"
        else:
            reason = "candidate_passes_filters_but_selection_by_max_q"

        results.append(CandidateResult(
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
        ))

    return results


def write_candidate_csv(path: str, rows: List[CandidateResult]) -> None:
    """输出所有候选组合结果。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
    """输出文本结果。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write("Stepwise Geodetector results\n")
        f.write("=" * 80 + "\n")
        f.write(f"lambda = {lam}\n")
        f.write(f"p_threshold = {p_threshold}\n")
        f.write(f"min_group_size = {min_group_size}（当前版本不剔除单样本分层）\n\n")

        f.write("[Selected path]\n")
        for r in selected_path:
            s_text = "" if r.s is None else f"{r.s:.6f}"
            dq_text = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            vr_ratio_text = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"
            f.write(
                f"Step {r.step}: {r.combination}\n"
                f"  added factor: {r.candidate_factor}\n"
                f"  q={r.q:.6f}, Δq={dq_text}, VR={r.vr:.6f}, VR_ratio={vr_ratio_text}, "
                f"S={s_text}, p={r.p:.6g}, n={r.n}, k={r.k}, "
                f"min_group_size={r.min_group_size}, max_group_size={r.max_group_size}\n"
                f"  raster: {r.raster_path}\n"
                f"  reason: {r.reason}\n\n"
            )

        f.write("\n[All candidate results]\n")
        for r in all_candidates:
            s_text = "" if r.s is None else f"{r.s:.6f}"
            dq_text = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            vr_ratio_text = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"
            f.write(
                f"Step {r.step} | {r.combination} | q={r.q:.6f}, Δq={dq_text}, "
                f"VR={r.vr:.6f}, VR_ratio={vr_ratio_text}, S={s_text}, "
                f"p={r.p:.6g}, k={r.k}, min_n={r.min_group_size}, "
                f"accepted={r.accepted}, reason={r.reason}\n"
            )


def read_input_file(txt_path: str) -> Dict:
    """
    读取输入文件。
    支持中文键：
      工作文件夹、值文件、输出文件夹、因子文件、lambda、p阈值、最小样本数
    """
    config = {
        "input_folder": "",
        "value_file": "",
        "factor_files": [],
        "output_folder": "stepwise_output",
        "lambda": 1,
        "p_threshold": 0.05,
        "min_group_size": 1,
    }

    with open(txt_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    in_factor_block = False
    for line in raw_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            in_factor_block = False

            if key in ["工作文件夹", "input_folder", "workspace"]:
                config["input_folder"] = value
            elif key in ["值文件", "value_file", "y", "dependent"]:
                config["value_file"] = value
            elif key in ["输出文件夹", "output_folder", "output"]:
                config["output_folder"] = value
            elif key in ["lambda", "λ", "lam", "lambda值"]:
                config["lambda"] = float(value)
            elif key in ["p阈值", "p_threshold", "pvalue", "p_value"]:
                config["p_threshold"] = float(value)
            elif key in ["最小样本数", "min_group_size", "min_n"]:
                config["min_group_size"] = int(value)
            elif key in ["因子文件", "factor_files", "factors"]:
                in_factor_block = True
                if value:
                    config["factor_files"].append(value)
            else:
                # 未识别的 key，作为因子文件兼容处理
                config["factor_files"].append(line)
        else:
            # 没有冒号的行，一般是因子文件名
            config["factor_files"].append(line)

    if not config["input_folder"]:
        config["input_folder"] = os.path.dirname(os.path.abspath(txt_path))
    if not config["value_file"]:
        raise ValueError("input.txt 中缺少：值文件")
    if not config["factor_files"]:
        raise ValueError("input.txt 中缺少：因子文件")

    return config


def resolve_path(base_folder: str, file_name: str) -> str:
    """相对路径自动拼接工作文件夹；绝对路径直接返回。"""
    return file_name if os.path.isabs(file_name) else os.path.join(base_folder, file_name)


def stepwise_geodetector(txt_path: str) -> None:
    """
    主函数：执行逐步 Geodetector 分析。
    """
    cfg = read_input_file(txt_path)

    input_folder = cfg["input_folder"]
    value_path = resolve_path(input_folder, cfg["value_file"])
    factor_paths = [resolve_path(input_folder, f) for f in cfg["factor_files"]]
    out_folder = resolve_path(input_folder, cfg["output_folder"])
    lam = float(cfg["lambda"])
    p_threshold = float(cfg["p_threshold"])
    min_group_size = int(cfg["min_group_size"])

    os.makedirs(out_folder, exist_ok=True)

    print("\n========== Stepwise Geodetector ==========")
    print(f"工作文件夹: {input_folder}")
    print(f"值文件: {value_path}")
    print(f"输出文件夹: {out_folder}")
    print(f"lambda: {lam}")
    print(f"p阈值: {p_threshold}")
    print(f"最小样本数参数: {min_group_size}（当前版本不剔除单样本分层）")
    print("候选因子:")
    for fp in factor_paths:
        print(f"  - {fp}")

    all_candidates: List[CandidateResult] = []
    selected_path: List[CandidateResult] = []

    # Step 1: 单因子筛选
    single_results = evaluate_single_factors(factor_paths, value_path, min_group_size=min_group_size)
    all_candidates.extend(single_results)

    initial = choose_initial_factor(single_results, p_threshold=p_threshold)
    selected_path.append(initial)

    print("\n[Step 1] 初始因子选择")
    print(f"选择: {initial.candidate_factor}, q={initial.q:.6f}, VR={initial.vr:.6f}, p={initial.p:.6g}, k={initial.k}")

    remaining = [fp for fp in factor_paths if factor_name(fp) != initial.candidate_factor]
    current_raster = initial.raster_path
    current_q = initial.q
    current_vr = initial.vr
    current_combo_names = [initial.candidate_factor]

    # Step 2+
    step = 2
    while remaining:
        print(f"\n[Step {step}] 评价剩余候选因子")
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

        # 选择逻辑：以 q 最大为准则选择候选因子；S 只用于判断是否接受该选择。
        # 先排除没有解释增益或统计不显著的候选组合，再在剩余组合中取 q 最大者。
        q_pool = [r for r in step_results if (r.delta_q > 0 and r.p <= p_threshold)]
        if not q_pool:
            print(f"[停止] Step {step} 没有候选因子同时满足 Δq>0 和 p<={p_threshold}")
            break

        best = max(q_pool, key=lambda r: r.q)

        # 对 q 最大候选因子进行 S 判断。若 S <= 0，则该步不再保留新因子，逐步过程停止。
        if best.s is None or best.s <= 0:
            best.accepted = False
            best.reason = "max_q_candidate_rejected_by_S"
            print(
                f"[停止] Step {step} 的最大 q 候选因子为 {best.candidate_factor}，"
                f"q={best.q:.6f}, Δq={best.delta_q:.6f}, VR={best.vr:.6f}, "
                f"VR_ratio={best.vr_ratio:.6f}, S={best.s:.6f}, p={best.p:.6g}；"
                f"由于 S<=0，不再保留新因子。"
            )
            break

        # q 最大且 S>0，保留该因子。
        best.accepted = True
        best.reason = "selected_by_max_q_retained_by_positive_S"
        for r in step_results:
            if r is not best and r.reason == "candidate_passes_filters_but_selection_by_max_q":
                r.reason = "not_selected_because_q_lower_than_selected_candidate"

        selected_path.append(best)

        print(
            f"选择: {best.candidate_factor}, q={best.q:.6f}, Δq={best.delta_q:.6f}, "
            f"VR={best.vr:.6f}, VR_ratio={best.vr_ratio:.6f}, S={best.s:.6f}, p={best.p:.6g}, k={best.k}"
        )

        current_raster = best.raster_path
        current_q = best.q
        current_vr = best.vr
        current_combo_names.append(best.candidate_factor)
        remaining = [fp for fp in remaining if factor_name(fp) != best.candidate_factor]
        step += 1

    # 输出结果
    candidate_csv = os.path.join(out_folder, "all_candidate_results.csv")
    selected_csv = os.path.join(out_folder, "selected_path.csv")
    summary_txt = os.path.join(out_folder, "result.txt")

    write_candidate_csv(candidate_csv, all_candidates)
    write_candidate_csv(selected_csv, selected_path)
    write_summary_txt(summary_txt, selected_path, all_candidates, lam, p_threshold, min_group_size)

    print("\n========== 完成 ==========")
    print(f"完整候选结果: {candidate_csv}")
    print(f"最终保留路径: {selected_csv}")
    print(f"文本报告: {summary_txt}")
    print("最终组合:", " ∩ ".join([r.candidate_factor for r in selected_path]))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        txt_path = sys.argv[1]
    else:
        txt_path = r".\input.txt"
    stepwise_geodetector(txt_path)

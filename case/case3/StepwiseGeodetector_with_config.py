# -*- coding: utf-8 -*-
import os
import math
import csv
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Tuple

import pandas as pd
import numpy as np
from scipy.stats import f




DEFAULT_CONFIG = {
    "input_excel": "synthetic_stepwise_geodetector_groups_123.xlsx",
    "output_folder": "synthetic_stepwise_output",
    "value_col": "Y",
    "factor_cols": ["X1", "X2", "X3"],
    "lam": 1,
    "p_threshold": 0.05,
    "min_group_size": 1,
    "verbose": True,
}


def write_default_config(config_path: str) -> None:
    """如果配置文件不存在，生成一个默认 config.json 模板。"""
    with open(config_path, "w", encoding="utf-8") as fobj:
        json.dump(DEFAULT_CONFIG, fobj, ensure_ascii=False, indent=2)


def load_config(config_path: str) -> dict:
    """读取 JSON 配置文件，并补全缺省参数。"""
    if not os.path.exists(config_path):
        write_default_config(config_path)
        raise FileNotFoundError(
            f"未找到配置文件，已自动生成模板: {config_path}\n"
            f"请检查 input_excel、output_folder、value_col 和 factor_cols 后重新运行。"
        )

    with open(config_path, "r", encoding="utf-8") as fobj:
        user_cfg = json.load(fobj)

    cfg = DEFAULT_CONFIG.copy()
    cfg.update(user_cfg)

    # 将相对路径解释为相对于配置文件所在目录
    config_dir = os.path.dirname(os.path.abspath(config_path))
    for key in ["input_excel", "output_folder"]:
        if cfg.get(key) and not os.path.isabs(str(cfg[key])):
            cfg[key] = os.path.join(config_dir, str(cfg[key]))

    return cfg


# =========================
# 数据结构
# =========================

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
    retained: bool
    reason: str


# =========================
# 基础函数
# =========================

def clean_name(x) -> str:
    """把列名/因子名转为安全字符串。"""
    return str(x).strip()


def calculate_geodetector_stats(
    df: pd.DataFrame,
    y_col: str,
    group_col: str,
    min_group_size: int = 2
) -> GeoDetectorStats:
    """
    使用平方和计算 q、VR(F)、p。

    q = 1 - SSW / SST
    VR = (SSB/(k-1)) / (SSW/(n-k))
    """
    data = df[[y_col, group_col]].dropna().copy()
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna(subset=[y_col, group_col]).copy()

    if data.empty:
        raise ValueError(f"{group_col} 没有有效样本。")

    # 去除字符串空值
    data[group_col] = data[group_col].astype(str)
    data = data[data[group_col].str.lower() != "nan"].copy()
    data = data[data[group_col].str.strip() != ""].copy()

    # 剔除样本数过小的分层
    if min_group_size > 1:
        counts0 = data.groupby(group_col)[y_col].count()
        keep_groups = counts0[counts0 >= min_group_size].index
        data = data[data[group_col].isin(keep_groups)].copy()

    n = int(len(data))
    k = int(data[group_col].nunique())

    if k < 2:
        raise ValueError(f"{group_col} 有效分层数 k < 2，无法计算。")
    if n <= k:
        raise ValueError(f"{group_col} 有效样本数 n <= k，无法计算 VR/F。n={n}, k={k}")

    y = data[y_col].astype(float)
    overall_mean = y.mean()

    # 总平方和 SST
    sst = float(((y - overall_mean) ** 2).sum())
    if sst <= 0:
        raise ValueError(f"{y_col} 总平方和 SST <= 0，无法计算 q。")

    # 组内平方和 SSW
    ssw = float(
        data.groupby(group_col)[y_col]
        .apply(lambda x: ((x.astype(float) - x.astype(float).mean()) ** 2).sum())
        .sum()
    )

    # 组间平方和 SSB
    ssb = max(float(sst - ssw), 0.0)

    q = 1.0 - ssw / sst

    if ssw <= 0:
        vr = float("inf")
        p_value = 0.0
    else:
        vr = (ssb / (k - 1)) / (ssw / (n - k))
        p_value = float(f.sf(vr, k - 1, n - k))

    counts = data.groupby(group_col)[y_col].count()

    return GeoDetectorStats(
        q=float(q),
        vr=float(vr),
        p=float(p_value),
        n=n,
        k=k,
        ssw=ssw,
        ssb=ssb,
        sst=sst,
        min_group_size=int(counts.min()),
        max_group_size=int(counts.max()),
    )


def make_interaction_column(
    df: pd.DataFrame,
    cols: List[str],
    new_col: str
) -> pd.DataFrame:
    """
    根据多个因子列生成交互分组，并重新编码为 1, 2, 3, ...
    缺失值所在行保留为 NaN，不参与后续计算。
    """
    out = df.copy()

    valid = out[cols].notna().all(axis=1)
    labels = pd.Series(np.nan, index=out.index, dtype="object")

    if valid.any():
        label_str = out.loc[valid, cols].astype(str).agg("__".join, axis=1)
        codes, _ = pd.factorize(label_str)
        labels.loc[valid] = codes + 1

    out[new_col] = labels
    return out


def safe_s_score(
    q_prev: float,
    vr_prev: float,
    q_new: float,
    vr_new: float,
    lam: float
) -> Tuple[float, float, float]:
    """计算 Δq、VR ratio 和 S。"""
    delta_q = q_new - q_prev

    if (
        vr_prev <= 0 or vr_new <= 0
        or not np.isfinite(vr_prev)
        or not np.isfinite(vr_new)
    ):
        vr_ratio = float("nan")
        s_value = float("-inf")
    else:
        vr_ratio = vr_new / vr_prev
        s_value = delta_q - lam * math.log(vr_ratio)

    return float(delta_q), float(vr_ratio), float(s_value)


def evaluate_single_factors(
    df: pd.DataFrame,
    y_col: str,
    factor_cols: List[str],
    min_group_size: int
) -> List[CandidateResult]:
    """Step 1：单因子计算 q、VR、p，不计算 S。"""
    results = []

    for col in factor_cols:
        stats = calculate_geodetector_stats(df, y_col, col, min_group_size=min_group_size)
        results.append(
            CandidateResult(
                step=1,
                candidate_factor=col,
                combination=col,
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
                retained=False,
                reason="single_factor_screening",
            )
        )

    return results


def choose_initial_factor(
    single_results: List[CandidateResult],
    p_threshold: float
) -> CandidateResult:
    """
    初始因子：优先在显著因子中选 q 最大；
    若没有显著因子，则选 q 最大并标记。
    """
    significant = [r for r in single_results if r.p <= p_threshold]
    pool = significant if significant else single_results

    best = max(pool, key=lambda r: r.q)
    best.retained = True
    best.reason = (
        "initial_selected_by_max_q"
        if significant
        else "initial_selected_by_max_q_no_significant_factor"
    )
    return best


def evaluate_step_candidates(
    df: pd.DataFrame,
    step: int,
    y_col: str,
    current_factors: List[str],
    remaining_factors: List[str],
    current_q: float,
    current_vr: float,
    lam: float,
    p_threshold: float,
    min_group_size: int,
) -> Tuple[List[CandidateResult], Dict[str, pd.Series]]:
    """
    Step 2+：当前组合与每个剩余因子生成交互列，并计算 q、VR、p、S。
    """
    results = []
    generated_groups = {}

    for cand in remaining_factors:
        combo = current_factors + [cand]
        combo_name = " ∩ ".join(combo)
        tmp_col = f"__step{step}_group__{cand}"

        tmp_df = make_interaction_column(df, combo, tmp_col)
        stats = calculate_geodetector_stats(tmp_df, y_col, tmp_col, min_group_size=min_group_size)

        delta_q, vr_ratio, s_value = safe_s_score(
            q_prev=current_q,
            vr_prev=current_vr,
            q_new=stats.q,
            vr_new=stats.vr,
            lam=lam,
        )

        if delta_q <= 0:
            reason = "rejected_delta_q_not_positive"
        elif stats.p > p_threshold:
            reason = "rejected_p_not_significant"
        elif s_value <= 0:
            reason = "candidate_max_q_may_be_rejected_by_S"
        else:
            reason = "candidate_passes_basic_filters"

        results.append(
            CandidateResult(
                step=step,
                candidate_factor=cand,
                combination=combo_name,
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
                retained=False,
                reason=reason,
            )
        )

        generated_groups[cand] = tmp_df[tmp_col]

    return results, generated_groups


def write_results_csv(path: str, rows: List[CandidateResult]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with open(path, "w", newline="", encoding="utf-8-sig") as fobj:
        writer = csv.DictWriter(fobj, fieldnames=fieldnames)
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
    y_col: str,
    factor_cols: List[str],
    lam: float,
    p_threshold: float,
    min_group_size: int,
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as fobj:
        fobj.write("Stepwise Geodetector Excel/XLS results\n")
        fobj.write("=" * 80 + "\n")
        fobj.write(f"Y column: {y_col}\n")
        fobj.write(f"Factor columns: {', '.join(factor_cols)}\n")
        fobj.write(f"lambda = {lam}\n")
        fobj.write(f"p_threshold = {p_threshold}\n")
        fobj.write(f"min_group_size = {min_group_size}\n")
        fobj.write("\nSelection rule:\n")
        fobj.write("  Step 1: select the significant single factor with the largest q.\n")
        fobj.write("  Step 2+: select the candidate with the largest q, then use S>0 as retention/stopping criterion.\n\n")

        fobj.write("[Selected path]\n")
        for r in selected_path:
            dq = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            ratio = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"
            s = "" if r.s is None else f"{r.s:.6f}"
            fobj.write(
                f"Step {r.step}: {r.combination}\n"
                f"  added factor: {r.candidate_factor}\n"
                f"  q={r.q:.6f}, Δq={dq}, VR={r.vr:.6f}, "
                f"VR_ratio={ratio}, S={s}, p={r.p:.6g}, "
                f"n={r.n}, k={r.k}, min_group_size={r.min_group_size}, "
                f"max_group_size={r.max_group_size}\n"
                f"  reason: {r.reason}\n\n"
            )

        fobj.write("\n[All candidate results]\n")
        for r in all_candidates:
            dq = "" if not np.isfinite(r.delta_q) else f"{r.delta_q:.6f}"
            ratio = "" if not np.isfinite(r.vr_ratio) else f"{r.vr_ratio:.6f}"
            s = "" if r.s is None else f"{r.s:.6f}"
            fobj.write(
                f"Step {r.step} | {r.combination} | "
                f"q={r.q:.6f}, Δq={dq}, VR={r.vr:.6f}, "
                f"VR_ratio={ratio}, S={s}, p={r.p:.6g}, "
                f"k={r.k}, min_n={r.min_group_size}, retained={r.retained}, "
                f"reason={r.reason}\n"
            )


def load_excel(path: str) -> pd.DataFrame:
    """读取 xls/xlsx。"""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".xls":
        # .xls 需要 xlrd
        return pd.read_excel(path, engine="xlrd")
    elif ext in [".xlsx", ".xlsm"]:
        # .xlsx 通常需要 openpyxl
        return pd.read_excel(path, engine="openpyxl")
    else:
        return pd.read_excel(path)


# =========================
# 主流程
# =========================

def stepwise_geodetector_excel(
    input_excel: str,
    output_folder: str,
    value_col: Optional[str] = None,
    factor_cols: Optional[List[str]] = None,
    lam: float = 0.1,
    p_threshold: float = 0.05,
    min_group_size: int = 2,
    verbose: bool = True,
) -> None:
    os.makedirs(output_folder, exist_ok=True)

    df = load_excel(input_excel)
    df.columns = [clean_name(c) for c in df.columns]

    if value_col is None:
        value_col = df.columns[0]
    else:
        value_col = clean_name(value_col)

    if factor_cols is None:
        factor_cols = list(df.columns)
        factor_cols.remove(value_col)
    else:
        factor_cols = [clean_name(c) for c in factor_cols]

    missing = [c for c in [value_col] + factor_cols if c not in df.columns]
    if missing:
        raise ValueError(f"以下列名不存在于 Excel 中: {missing}")

    if verbose:
        print("\n========== Stepwise Geodetector Excel/XLS ==========")
        print(f"输入文件: {input_excel}")
        print(f"输出文件夹: {output_folder}")
        print(f"Y列: {value_col}")
        print(f"候选因子: {factor_cols}")
        print(f"lambda: {lam}")
        print(f"p阈值: {p_threshold}")
        print(f"最小分层样本数: {min_group_size}")

    all_candidates: List[CandidateResult] = []
    selected_path: List[CandidateResult] = []

    # 保存每一步保留组合的分组列
    output_df = df.copy()

    # Step 1
    single_results = evaluate_single_factors(
        df=df,
        y_col=value_col,
        factor_cols=factor_cols,
        min_group_size=min_group_size,
    )
    all_candidates.extend(single_results)

    initial = choose_initial_factor(single_results, p_threshold=p_threshold)
    selected_path.append(initial)

    step1_col = "__step1_selected_group"
    output_df[step1_col] = df[initial.candidate_factor]

    if verbose:
        print("\n[Step 1] 单因子筛选")
        for r in single_results:
            print(f"  {r.candidate_factor}: q={r.q:.6f}, VR={r.vr:.6f}, p={r.p:.6g}, k={r.k}")
        print(f"选择初始因子: {initial.candidate_factor}, q={initial.q:.6f}")

    current_factors = [initial.candidate_factor]
    current_q = initial.q
    current_vr = initial.vr
    remaining = [c for c in factor_cols if c != initial.candidate_factor]

    # Step 2+
    step = 2
    while remaining:
        if verbose:
            print(f"\n[Step {step}] 候选交互组合")

        step_results, group_cols = evaluate_step_candidates(
            df=df,
            step=step,
            y_col=value_col,
            current_factors=current_factors,
            remaining_factors=remaining,
            current_q=current_q,
            current_vr=current_vr,
            lam=lam,
            p_threshold=p_threshold,
            min_group_size=min_group_size,
        )
        all_candidates.extend(step_results)

        if verbose:
            for r in step_results:
                print(
                    f"  + {r.candidate_factor}: q={r.q:.6f}, Δq={r.delta_q:.6f}, "
                    f"VR={r.vr:.6f}, VR_ratio={r.vr_ratio:.6f}, S={r.s:.6f}, "
                    f"p={r.p:.6g}, k={r.k}, reason={r.reason}"
                )

        # 关键规则：
        # 先以最大 q 作为选择准则；S 只判断取舍，不用于排序。
        q_pool = [r for r in step_results if (r.delta_q > 0 and r.p <= p_threshold)]

        if not q_pool:
            if verbose:
                print(f"[停止] Step {step}: 没有候选因子满足 Δq>0 且 p<={p_threshold}。")
            break

        best = max(q_pool, key=lambda r: r.q)

        if best.s is None or best.s <= 0:
            best.retained = False
            best.reason = "selected_by_max_q_but_rejected_by_S_stop"
            if verbose:
                print(
                    f"[停止] Step {step}: q 最大候选为 {best.candidate_factor}，"
                    f"但 S={best.s:.6f} <= 0，不保留并停止。"
                )
            break

        best.retained = True
        best.reason = "selected_by_max_q_and_retained_by_positive_S"
        selected_path.append(best)

        # 保存本步骤最终保留组合的交互分组
        selected_group_col = f"__step{step}_selected_group"
        output_df[selected_group_col] = group_cols[best.candidate_factor]

        if verbose:
            print(
                f"选择并保留: {best.candidate_factor}, "
                f"组合={best.combination}, q={best.q:.6f}, S={best.s:.6f}"
            )

        current_factors.append(best.candidate_factor)
        current_q = best.q
        current_vr = best.vr
        remaining = [c for c in remaining if c != best.candidate_factor]
        step += 1

    # 输出
    all_csv = os.path.join(output_folder, "all_candidate_results.csv")
    selected_csv = os.path.join(output_folder, "selected_path.csv")
    summary_txt = os.path.join(output_folder, "result.txt")
    grouped_csv = os.path.join(output_folder, "data_with_stepwise_groups.csv")
    grouped_xlsx = os.path.join(output_folder, "data_with_stepwise_groups.xlsx")

    write_results_csv(all_csv, all_candidates)
    write_results_csv(selected_csv, selected_path)
    write_summary_txt(
        summary_txt,
        selected_path,
        all_candidates,
        value_col,
        factor_cols,
        lam,
        p_threshold,
        min_group_size,
    )

    output_df.to_csv(grouped_csv, index=False, encoding="utf-8-sig")

    # xlsx 输出需要 openpyxl；如果没安装，不影响 csv 和结果输出
    try:
        output_df.to_excel(grouped_xlsx, index=False, engine="openpyxl")
        xlsx_msg = grouped_xlsx
    except ModuleNotFoundError:
        xlsx_msg = "未输出 xlsx：缺少 openpyxl。可运行 pip install openpyxl"
    except Exception as e:
        xlsx_msg = f"未输出 xlsx：{e}"

    if verbose:
        print("\n========== 完成 ==========")
        print(f"所有候选结果: {all_csv}")
        print(f"最终保留路径: {selected_csv}")
        print(f"文本报告: {summary_txt}")
        print(f"带分组结果 CSV: {grouped_csv}")
        print(f"带分组结果 XLSX: {xlsx_msg}")
        print("最终组合:", " ∩ ".join([r.candidate_factor for r in selected_path]))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run stepwise Geodetector using a JSON configuration file."
    )
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
        help="Path to config.json. Default: config.json in the same folder as this script.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    if cfg.get("verbose", True):
        print("\n========== Loaded configuration ==========")
        for key, value in cfg.items():
            print(f"{key}: {value}")

    stepwise_geodetector_excel(
        input_excel=cfg["input_excel"],
        output_folder=cfg["output_folder"],
        value_col=cfg.get("value_col"),
        factor_cols=cfg.get("factor_cols"),
        lam=float(cfg.get("lam", 1)),
        p_threshold=float(cfg.get("p_threshold", 0.05)),
        min_group_size=int(cfg.get("min_group_size", 1)),
        verbose=bool(cfg.get("verbose", True)),
    )


if __name__ == "__main__":
    main()

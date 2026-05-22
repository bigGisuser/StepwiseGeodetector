# -*- coding: utf-8 -*-
"""
Create violin plots from a continuous value raster and categorical label rasters.

This version supports command-line arguments, a JSON configuration file, and a working directory for relative paths.

Examples
--------
1) Run with a configuration file:
   python violinplot_params_config.py --config violinplot_config.json

2) Run a single plot from the command line:
   python violinplot_params_config.py ^
       --value-raster data/Case2/LSD.tif ^
       --label-raster data/Case2/VEG.tif ^
       --output outputs/figures/violin_VEG.png ^
       --x-label "Vegetation class" ^
       --y-label "Landslide density"
"""

import argparse
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from osgeo import gdal


def read_raster(raster_path: str):
    """Read the first band of a raster file."""
    raster_data = gdal.Open(raster_path)
    if raster_data is None:
        raise FileNotFoundError(f"Cannot open raster file: {raster_path}")

    raster_geotrans = raster_data.GetGeoTransform()
    raster_proj = raster_data.GetProjection()
    x_size = raster_data.RasterXSize
    y_size = raster_data.RasterYSize

    band = raster_data.GetRasterBand(1)
    nodata_value = band.GetNoDataValue()
    data = band.ReadAsArray()

    return data, (raster_geotrans, raster_proj, x_size, y_size, nodata_value)


def build_plot_dataframe(
    value_raster_path: str,
    label_raster_path: str,
    ignore_label_zero: bool = True,
    ignore_value_nodata: bool = True,
) -> pd.DataFrame:
    """Convert paired value and label rasters into a long-format DataFrame."""
    value_data, value_meta = read_raster(value_raster_path)
    label_data, label_meta = read_raster(label_raster_path)

    if value_data.shape != label_data.shape:
        raise ValueError(
            "The value raster and label raster have different shapes: "
            f"value={value_data.shape}, label={label_data.shape}. "
            "Please resample them to the same grid before plotting."
        )

    value_nodata = value_meta[-1]
    label_nodata = label_meta[-1]

    valid_mask = np.ones(value_data.shape, dtype=bool)

    if label_nodata is not None:
        valid_mask &= label_data != label_nodata
    if ignore_label_zero:
        valid_mask &= label_data != 0

    if ignore_value_nodata and value_nodata is not None:
        valid_mask &= value_data != value_nodata

    # Only apply isnan to numeric arrays. GDAL usually returns numeric arrays.
    if np.issubdtype(value_data.dtype, np.floating):
        valid_mask &= ~np.isnan(value_data)
    if np.issubdtype(label_data.dtype, np.floating):
        valid_mask &= ~np.isnan(label_data)

    labels = label_data[valid_mask]
    values = value_data[valid_mask]

    if labels.size == 0:
        raise ValueError("No valid raster cells were found for plotting.")

    plot_df = pd.DataFrame({"label": labels, "value": values})
    plot_df = plot_df.sort_values("label")
    return plot_df


def create_violin_plot(
    plot_df: pd.DataFrame,
    output_path: str,
    x_label: str = "Class",
    y_label: str = "Value",
    title: Optional[str] = None,
    width_cm: float = 5.0,
    height_cm: float = 3.0,
    dpi: int = 600,
    font_family: str = "Arial",
    font_size: int = 6,
    palette: str = "Set2",
    show_quartile: bool = True,
) -> None:
    """Create and save a violin plot."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    plt.rcParams.update({
        "font.family": font_family,
        "font.size": font_size,
        "axes.labelsize": font_size,
        "axes.titlesize": font_size,
    })

    fig, ax = plt.subplots(figsize=(width_cm / 2.54, height_cm / 2.54), dpi=dpi)
    inner_style = "quartile" if show_quartile else None

    sns.violinplot(
        x="label",
        y="value",
        data=plot_df,
        inner=inner_style,
        palette=palette,
        linewidth=0.5,
        ax=ax,
        hue="label",
        legend=False,
    )

    ax.set_xlabel(x_label, fontsize=font_size, fontweight="bold")
    ax.set_ylabel(y_label, fontsize=font_size, fontweight="bold")

    if title:
        ax.set_title(title, fontsize=font_size, fontweight="bold")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    ax.set_facecolor("white")

    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load a JSON configuration file."""
    if not config_path:
        return {}

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Cannot find config file: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_working_dir(config: Dict[str, Any], config_path: Optional[str], cli_working_dir: Optional[str]) -> str:
    """Resolve the base working directory used for all relative paths.

    Priority:
    1. --working-dir from the command line;
    2. working_dir in the JSON configuration file;
    3. the folder containing the configuration file;
    4. the current command-line directory.
    """
    if cli_working_dir:
        base_dir = cli_working_dir
    elif config.get("working_dir"):
        base_dir = config["working_dir"]
    elif config_path:
        base_dir = os.path.dirname(os.path.abspath(config_path))
    else:
        base_dir = os.getcwd()

    return os.path.abspath(os.path.expanduser(base_dir))


def resolve_path(path_value: Optional[str], working_dir: str) -> Optional[str]:
    """Convert a relative path to an absolute path based on working_dir."""
    if path_value is None:
        return None

    path_str = os.path.expanduser(str(path_value))
    if os.path.isabs(path_str):
        return os.path.abspath(path_str)
    return os.path.abspath(os.path.join(working_dir, path_str))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create violin plots from a value raster and categorical label raster(s)."
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Path to a JSON configuration file. If provided, values in the file are used as defaults.",
    )
    parser.add_argument(
        "--working-dir",
        default=None,
        help="Base working directory for relative input and output paths. Overrides working_dir in the config.",
    )
    parser.add_argument("--value-raster", default=None, help="Path to the value raster, e.g., LSD.tif.")
    parser.add_argument("--label-raster", default=None, help="Path to one categorical label raster.")
    parser.add_argument("--output", default=None, help="Output figure path for a single plot.")
    parser.add_argument("--x-label", default=None, help="X-axis label.")
    parser.add_argument("--y-label", default=None, help="Y-axis label.")
    parser.add_argument("--title", default=None, help="Optional figure title.")
    parser.add_argument("--width-cm", type=float, default=None, help="Figure width in centimeters.")
    parser.add_argument("--height-cm", type=float, default=None, help="Figure height in centimeters.")
    parser.add_argument("--dpi", type=int, default=None, help="Output figure resolution.")
    parser.add_argument("--font-family", default=None, help="Font family.")
    parser.add_argument("--font-size", type=int, default=None, help="Font size.")
    parser.add_argument("--palette", default=None, help="Seaborn color palette.")
    parser.add_argument("--keep-label-zero", action="store_true", help="Keep label value 0.")
    parser.add_argument("--no-quartile", action="store_true", help="Do not show quartile lines.")

    # Correct position: parser.parse_args() must be inside this function.
    return parser.parse_args()


def config_get(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    return config[key] if key in config else default


def make_single_plot(task: Dict[str, Any], common: Dict[str, Any]) -> None:
    working_dir = common.get("working_dir", os.getcwd())
    value_raster = resolve_path(task.get("value_raster") or common.get("value_raster"), working_dir)
    label_raster = resolve_path(task.get("label_raster"), working_dir)
    output = resolve_path(task.get("output"), working_dir)

    if not value_raster:
        raise ValueError("Missing value_raster. Set it in the config or use --value-raster.")
    if not label_raster:
        raise ValueError("Missing label_raster. Set it in the config or use --label-raster.")
    if not output:
        raise ValueError("Missing output. Set it in the config or use --output.")

    ignore_label_zero = bool(common.get("ignore_label_zero", True))
    show_quartile = bool(common.get("show_quartile", True))

    plot_df = build_plot_dataframe(
        value_raster_path=value_raster,
        label_raster_path=label_raster,
        ignore_label_zero=ignore_label_zero,
    )

    create_violin_plot(
        plot_df=plot_df,
        output_path=output,
        x_label=task.get("x_label", common.get("x_label", "Class")),
        y_label=task.get("y_label", common.get("y_label", "Value")),
        title=task.get("title", common.get("title")),
        width_cm=float(task.get("width_cm", common.get("width_cm", 5.0))),
        height_cm=float(task.get("height_cm", common.get("height_cm", 3.0))),
        dpi=int(task.get("dpi", common.get("dpi", 600))),
        font_family=task.get("font_family", common.get("font_family", "Arial")),
        font_size=int(task.get("font_size", common.get("font_size", 6))),
        palette=task.get("palette", common.get("palette", "Set2")),
        show_quartile=show_quartile,
    )

    print(f"Done. Figure saved to: {output}")
    print(f"Number of valid samples: {len(plot_df)}")
    print("Samples by label:")
    print(plot_df.groupby("label")["value"].count())
    print("-" * 60)


def main() -> None:
    args = parse_args()
    config_path = os.path.abspath(args.config) if args.config else None
    config = load_config(config_path)
    working_dir = resolve_working_dir(config, config_path, args.working_dir)

    common = {
        "working_dir": working_dir,
        "value_raster": args.value_raster or config_get(config, "value_raster"),
        "x_label": args.x_label or config_get(config, "x_label", "Class"),
        "y_label": args.y_label or config_get(config, "y_label", "Value"),
        "title": args.title or config_get(config, "title", None),
        "width_cm": args.width_cm if args.width_cm is not None else config_get(config, "width_cm", 5.0),
        "height_cm": args.height_cm if args.height_cm is not None else config_get(config, "height_cm", 3.0),
        "dpi": args.dpi if args.dpi is not None else config_get(config, "dpi", 600),
        "font_family": args.font_family or config_get(config, "font_family", "Arial"),
        "font_size": args.font_size if args.font_size is not None else config_get(config, "font_size", 6),
        "palette": args.palette or config_get(config, "palette", "Set2"),
        "ignore_label_zero": not args.keep_label_zero if args.keep_label_zero else config_get(config, "ignore_label_zero", True),
        "show_quartile": not args.no_quartile if args.no_quartile else config_get(config, "show_quartile", True),
    }

    print(f"Working directory: {working_dir}")

    # Config mode: create multiple plots.
    if "plots" in config and config["plots"]:
        for task in config["plots"]:
            make_single_plot(task, common)
        return

    # Command-line or simple-config single-plot mode.
    task = {
        "value_raster": common.get("value_raster"),
        "label_raster": args.label_raster or config_get(config, "label_raster"),
        "output": args.output or config_get(config, "output"),
        "x_label": common.get("x_label"),
        "y_label": common.get("y_label"),
        "title": common.get("title"),
        "width_cm": common.get("width_cm"),
        "height_cm": common.get("height_cm"),
        "dpi": common.get("dpi"),
        "font_family": common.get("font_family"),
        "font_size": common.get("font_size"),
        "palette": common.get("palette"),
    }
    make_single_plot(task, common)


if __name__ == "__main__":
    main()

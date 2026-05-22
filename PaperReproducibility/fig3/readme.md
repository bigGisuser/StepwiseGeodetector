# Figure 3 Reproduction Guide: Input Data Preparation and Violin Plot Generation

## 1. Purpose

Figure 3 shows the distribution of landslide density across the classes of each candidate factor. To reproduce this figure, the original raster, polygon, line, and point data should first be converted into a unified 2000 m grid. The generated raster layers are then used as the input data for the violin-plot script.

The violin plots are generated from one continuous value raster and eight categorical label rasters:

- value raster: `LSD.tif`
- label rasters: `VEG.tif`, `PGA.tif`, `DEM.tif`, `ASP.tif`, `SLP.tif`, `FAULT.tif`, `HYD.tif`, and `LRD.tif`

All paths are relative paths.

---

## 2. Recommended folder structure

```text
Case2_Landslide/
│
├─ violinplot_params_config.py
├─ violinplot_config.json
│
├─ input/
│  ├─ LSD.tif
│  ├─ VEG.tif
│  ├─ PGA.tif
│  ├─ DEM.tif
│  ├─ ASP.tif
│  ├─ SLP.tif
│  ├─ FAULT.tif
│  ├─ HYD.tif
│  └─ LRD.tif
│
└─ output/
   └─ figures/
      ├─ violin_VEG.png
      ├─ violin_PGA.png
      ├─ violin_DEM.png
      ├─ violin_ASP.png
      ├─ violin_SLP.png
      ├─ violin_FAULT.png
      ├─ violin_HYD.png
      └─ violin_ROAD.png
```

---

## 3. Input data preparation

All datasets should be aligned to the same projection, extent, cell size, number of rows and columns, and grid origin. The target spatial resolution is 2000 m.

### 3.1 Landslide density raster

The landslide point dataset is converted to a landslide-density raster using kernel density estimation.

| Item | Setting |
|---|---|
| Input data | landslide point layer |
| Output raster | `input/LSD.tif` |
| Method | Kernel Density |
| Cell size | 2000 m |
| Search radius | 10000 m |
| Other parameters | Default settings |

This raster is used as the dependent variable for Figure 3.

### 3.2 Raster factors

The original raster factors are resampled to 2000 m using bilinear interpolation and then reclassified into five classes.

| Factor | Output raster | Resampling method | Cell size | Breakpoints |
|---|---|---|---:|---|
| PGA | `input/PGA.tif` | Bilinear | 2000 m | 0.110, 0.145, 0.180, 0.220 |
| Elevation | `input/DEM.tif` | Bilinear | 2000 m | 2350, 3200, 4020, 5100 |
| Aspect | `input/ASP.tif` | Bilinear | 2000 m | 45, 135, 225, 315 |
| Slope gradient | `input/SLP.tif` | Bilinear | 2000 m | 18.7, 30.4, 40.3, 52.2 |

The output factor rasters should contain categorical integer labels. Invalid or background cells can be coded as 0 or NoData.

### 3.3 Line factors

Road, fault, and river line layers are converted to density rasters using kernel density estimation. The density rasters are then reclassified into five classes.

| Factor | Output raster | Method | Cell size | Search radius | Breakpoints |
|---|---|---|---:|---:|---|
| Road density | `input/LRD.tif` | Kernel Density | 2000 m | 10000 m | 0.032, 0.083, 0.137, 0.217 |
| Fault density | `input/FAULT.tif` | Kernel Density | 2000 m | 10000 m | 0.032, 0.078, 0.123, 0.175 |
| River density | `input/HYD.tif` | Kernel Density | 2000 m | 10000 m | 0.156, 0.282, 0.363, 0.431 |

Other kernel density parameters are kept as the default settings of the GIS software.

### 3.4 Vegetation polygon factor

The vegetation polygon layer is converted or resampled to a 2000 m categorical raster.

| Item | Setting |
|---|---|
| Input data | vegetation polygon layer |
| Output raster | `input/VEG.tif` |
| Cell size | 2000 m |
| Coding rule | non-vegetated areas are coded as 0 |

The vegetation raster should be aligned with `LSD.tif` and the other factor rasters.

---

## 4. Check before plotting

Before running the violin-plot script, confirm that all input rasters have:

1. the same projection;
2. the same extent;
3. the same cell size: 2000 m;
4. the same number of rows and columns;
5. the same grid origin;
6. categorical integer labels for factor rasters;
7. valid landslide-density values in `LSD.tif`.

The plotting script will stop with an error if the value raster and label raster have different shapes.

---

## 5. Violin plot configuration

Use the following configuration file:

```json
{
  "working_dir": "input",
  "value_raster": "LSD.tif",
  "y_label": "Landslide density",
  "width_cm": 5.0,
  "height_cm": 3.0,
  "dpi": 600,
  "font_family": "Arial",
  "font_size": 6,
  "palette": "Set2",
  "ignore_label_zero": true,
  "show_quartile": true,
  "plots": [
    {
      "label_raster": "VEG.tif",
      "output": "../output/figures/violin_VEG.png",
      "x_label": "Vegetation class",
      "title": "Vegetation cover"
    },
    {
      "label_raster": "PGA.tif",
      "output": "../output/figures/violin_PGA.png",
      "x_label": "PGA class",
      "title": "PGA"
    },
    {
      "label_raster": "DEM.tif",
      "output": "../output/figures/violin_DEM.png",
      "x_label": "Elevation class",
      "title": "Elevation"
    },
    {
      "label_raster": "ASP.tif",
      "output": "../output/figures/violin_ASP.png",
      "x_label": "Aspect class",
      "title": "Aspect"
    },
    {
      "label_raster": "SLP.tif",
      "output": "../output/figures/violin_SLP.png",
      "x_label": "Slope class",
      "title": "Slope"
    },
    {
      "label_raster": "FAULT.tif",
      "output": "../output/figures/violin_FAULT.png",
      "x_label": "Fault density class",
      "title": "Fault density"
    },
    {
      "label_raster": "HYD.tif",
      "output": "../output/figures/violin_HYD.png",
      "x_label": "River density class",
      "title": "River density"
    },
    {
      "label_raster": "LRD.tif",
      "output": "../output/figures/violin_ROAD.png",
      "x_label": "Road density class",
      "title": "Road density"
    }
  ]
}
```

---

## 6. Run the violin-plot script

From the `Case2_Landslide/` folder, run:

```bash
python violinplot_params_config.py --config violinplot_config.json
```

The script reads `input/LSD.tif` as the value raster and then uses each factor raster as a categorical grouping raster. Cells with label value 0 are ignored because `ignore_label_zero` is set to `true`.

---

## 7. Output files

The script generates the following files:

```text
output/figures/violin_VEG.png
output/figures/violin_PGA.png
output/figures/violin_DEM.png
output/figures/violin_ASP.png
output/figures/violin_SLP.png
output/figures/violin_FAULT.png
output/figures/violin_HYD.png
output/figures/violin_ROAD.png
```

These eight plots are then arranged into Figure 3 in the manuscript.

The panel order is:

- (A) elevation;
- (B) aspect;
- (C) slope;
- (D) fault;
- (E) river;
- (F) PGA;
- (G) road;
- (H) vegetation cover.


import numpy as np

from ssr_eval.ext.vissat_toolset_visualization.plot_height_map import (
    plot_height_map,
)
from ssr_eval.ext.vissat_toolset_lib.dsm_util import write_dsm_tif
from ssr_eval.ssr_toolset.proj_to_grid import proj_to_grid

import cv2


# points is in the cooridnate system (UTM east, UTM north, altitude)
def produce_dsm_from_points(
    bbx, points, tif_to_write, jpg_to_write, fill_small_holes
):
    # write dsm to tif
    ul_e = bbx["ul_easting"]
    ul_n = bbx["ul_northing"]

    e_resolution = 0.5  # 0.5 meters per pixel
    n_resolution = 0.5
    e_size = int(bbx["width"] / e_resolution) + 1
    n_size = int(bbx["height"] / n_resolution) + 1
    dsm = proj_to_grid(
        points,
        ul_e,
        ul_n,
        e_resolution,
        n_resolution,
        e_size,
        n_size,
        fill_small_holes,
    )
    # median filter
    dsm = cv2.medianBlur(dsm.astype(np.float32), 3)
    write_dsm_tif(
        dsm,
        tif_to_write,
        (ul_e, ul_n, e_resolution, n_resolution),
        (bbx["zone_number"], bbx["hemisphere"]),
        nodata_val=-9999,
    )

    # create a preview file
    if jpg_to_write is not None:
        dsm = np.clip(dsm, bbx["alt_min"], bbx["alt_max"])
        plot_height_map(dsm, jpg_to_write, save_cbar=True)

    return (ul_e, ul_n, e_size, n_size, e_resolution, n_resolution)

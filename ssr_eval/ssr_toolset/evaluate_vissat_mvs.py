import os
import json
import numpy as np

from ssr_eval.ext.vissat_toolset_lib.ply_np_converter import ply2np, np2ply
from ssr_eval.ext.vissat_toolset_lib.latlon_utm_converter import (
    latlon_to_eastnorh,
)
from ssr_eval.ext.vissat_toolset_lib.latlonalt_enu_converter import (
    enu_to_latlonalt,
)

from ssr_eval.ssr_toolset.evaluate import evaluate
from ssr_eval.ssr_toolset.produce_dsm import produce_dsm_from_points


def evaluate_point_cloud(
    site_data_dir, in_ply, out_dir, fill_small_holes, max_processes=4
):
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # load aoi.json from the site_data_dir
    with open(os.path.join(site_data_dir, "aoi.json")) as fp:
        bbx = json.load(fp)

    lat0 = (bbx["lat_min"] + bbx["lat_max"]) / 2.0
    lon0 = (bbx["lon_min"] + bbx["lon_max"]) / 2.0
    alt0 = bbx["alt_min"]

    # load input ply file
    points, color, comments = ply2np(in_ply)

    # convert to UTM coordinate system
    lat, lon, alt = enu_to_latlonalt(
        points[:, 0:1], points[:, 1:2], points[:, 2:3], lat0, lon0, alt0
    )
    east, north = latlon_to_eastnorh(lat, lon)
    points = np.hstack((east, north, alt))

    # write to ply file
    ply_to_write = os.path.join(out_dir, "point_cloud.ply")
    print("Writing to {}...".format(ply_to_write))
    comment_1 = "projection: UTM {}{}".format(
        bbx["zone_number"], bbx["hemisphere"]
    )
    np2ply(
        points,
        ply_to_write,
        color=color,
        comments=[
            comment_1,
        ],
        use_double=True,
    )

    # produce dsm and write to tif file
    tif_to_write = os.path.join(out_dir, "dsm.tif")
    jpg_to_write = os.path.join(out_dir, "dsm.jpg")
    print("Writing to {} and {}...".format(tif_to_write, jpg_to_write))
    produce_dsm_from_points(
        bbx, points, tif_to_write, jpg_to_write, fill_small_holes
    )

    tif_gt = os.path.join(site_data_dir, "ground_truth.tif")
    print("Evaluating {} with ground-truth {}...".format(tif_to_write, tif_gt))
    median_err, completeness = evaluate(
        tif_to_write, tif_gt, out_dir, max_processes
    )
    return median_err, completeness


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VisSat Toolset")
    parser.add_argument(
        "--data_dir", type=str, help="data directory for the site"
    )
    parser.add_argument(
        "--ply", type=str, help="recontructed point cloud in ply format"
    )
    parser.add_argument("--out_dir", type=str, help="output directory")
    parser.add_argument(
        "--eval",
        action="store_true",
        help="if turned on, the program will also output metric numbers",
    )
    parser.add_argument(
        "--max_processes",
        type=int,
        default=4,
        help="maximum number of processes to be launched",
    )

    args = parser.parse_args()
    evaluate_point_cloud(
        args.data_dir, args.ply, args.out_dir, args.eval, args.max_processes
    )

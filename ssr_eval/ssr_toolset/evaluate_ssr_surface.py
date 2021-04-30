import os
import json
import numpy as np

from ssr_eval.ext.vissat_toolset_lib.latlon_utm_converter import (
    latlon_to_eastnorh,
)
from ssr_eval.ext.vissat_toolset_lib.latlonalt_enu_converter import (
    enu_to_latlonalt,
)

# Important: The "evaluate" import MUST BE CALLED BEFORE "Pyntcloud", in order
# to properly execute "matplotlib.use('Agg')" in "evaluate"
from ssr_eval.ssr_toolset.evaluate import evaluate
from ssr_eval.ssr_toolset.produce_dsm import produce_dsm_from_points
from pyntcloud import PyntCloud


def evaluate_mesh(
    site_data_dir,
    in_ply,  # Reconstructed Mesh
    out_dir,
    fill_small_holes,
    max_processes=4,
    write_mesh=True,
):
    print("Run main_mesh: ...")

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # load aoi.json from the site_data_dir
    with open(os.path.join(site_data_dir, "aoi.json")) as fp:
        bbx = json.load(fp)

    lat0 = (bbx["lat_min"] + bbx["lat_max"]) / 2.0
    lon0 = (bbx["lon_min"] + bbx["lon_max"]) / 2.0
    alt0 = bbx["alt_min"]

    mesh = PyntCloud.from_file(in_ply)
    mesh_points = mesh.points.loc[:, ["x", "y", "z"]].to_numpy()

    # convert to UTM coordinate system
    lat, lon, alt = enu_to_latlonalt(
        mesh_points[:, 0:1],
        mesh_points[:, 1:2],
        mesh_points[:, 2:3],
        lat0,
        lon0,
        alt0,
    )
    east, north = latlon_to_eastnorh(lat, lon)
    mesh_points = np.hstack((east, north, alt))

    # write to ply file
    ply_to_write = os.path.join(out_dir, "point_cloud.ply")
    print("Writing to {}...".format(ply_to_write))
    comment_1 = "projection: UTM {}{}".format(
        bbx["zone_number"], bbx["hemisphere"]
    )

    also_save = []
    if write_mesh and hasattr(mesh, "mesh"):
        also_save.append("mesh")
    if hasattr(mesh, "comments"):
        also_save.append("comments")
    mesh.points.loc[:, ["x", "y", "z"]] = mesh_points
    mesh.to_file(ply_to_write, also_save=also_save)

    # produce dsm and write to tif file
    mesh_tif_to_write = os.path.join(out_dir, "dsm.tif")
    mesh_jpg_to_write = os.path.join(out_dir, "dsm.jpg")
    print(f"Writing to {mesh_tif_to_write} and {mesh_jpg_to_write}...")
    produce_dsm_from_points(
        bbx,
        mesh_points,
        mesh_tif_to_write,
        mesh_jpg_to_write,
        fill_small_holes,
    )

    gt_tif = os.path.join(site_data_dir, "ground_truth.tif")
    print(f"Evaluating {mesh_tif_to_write} with ground-truth {gt_tif}...")
    median_err, completeness = evaluate(
        mesh_tif_to_write, gt_tif, out_dir, max_processes
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
    main(args.data_dir, args.ply, args.out_dir, args.eval, args.max_processes)

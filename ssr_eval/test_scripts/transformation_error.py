import os
import json
import numpy as np
from pyntcloud import PyntCloud

from ssr_eval.ext.vissat_toolset_lib.latlon_utm_converter import (
    latlon_to_eastnorh,
    eastnorth_to_latlon,
)
from ssr_eval.ext.vissat_toolset_lib.latlonalt_enu_converter import (
    enu_to_latlonalt,
    latlonalt_to_enu,
)


def enu_to_eastnorth(site_data_dir, in_ply, transformed_ply):

    print("enu_to_eastnorth: ...")
    # load aoi.json from the site_data_dir
    with open(os.path.join(site_data_dir, "aoi.json")) as fp:
        bbx = json.load(fp)

    lat0 = (bbx["lat_min"] + bbx["lat_max"]) / 2.0
    lon0 = (bbx["lon_min"] + bbx["lon_max"]) / 2.0
    alt0 = bbx["alt_min"]

    mesh = PyntCloud.from_file(in_ply)
    points = mesh.points.loc[:, ["x", "y", "z"]].to_numpy()

    # convert to UTM coordinate system
    e = points[:, 0:1]
    n = points[:, 1:2]
    u = points[:, 2:3]

    lat, lon, alt = enu_to_latlonalt(e, n, u, lat0, lon0, alt0)
    east, north = latlon_to_eastnorh(lat, lon)
    points = np.hstack((east, north, alt))

    # print("e", e)
    # print("n", n)
    # print("u", u)
    # print("lat", lat)
    # print("lon", lon)
    # print("alt", alt)
    # print("east", east)
    # print("north", north)

    also_save = []
    if hasattr(mesh, "mesh"):
        also_save.append("mesh")
    if hasattr(mesh, "comments"):
        also_save.append("comments")
    mesh.points.loc[:, ["x", "y", "z"]] = points
    mesh.to_file(transformed_ply, also_save=also_save)

    print("enu_to_eastnorth: Done")


def eastnorth_to_enu(site_data_dir, transformed_ply, back_transformed_ply):

    print("eastnorth_to_enu: ...")

    # load aoi.json from the site_data_dir
    with open(os.path.join(site_data_dir, "aoi.json")) as fp:
        bbx = json.load(fp)

    lat0 = (bbx["lat_min"] + bbx["lat_max"]) / 2.0
    lon0 = (bbx["lon_min"] + bbx["lon_max"]) / 2.0
    alt0 = bbx["alt_min"]
    zone_number = bbx["zone_number"]
    hemisphere = bbx["hemisphere"]

    mesh = PyntCloud.from_file(transformed_ply)
    points = mesh.points.loc[:, ["x", "y", "z"]].to_numpy()
    east = points[:, 0:1]
    north = points[:, 1:2]
    alt = points[:, 2:3]
    # convert back to enu coordinates
    lat, lon = eastnorth_to_latlon(east, north, zone_number, hemisphere)
    e, n, u = latlonalt_to_enu(lat, lon, alt, lat0, lon0, alt0)
    points = np.hstack((e, n, u))

    # print("e", e)
    # print("n", n)
    # print("u", u)
    # print("lat", lat)
    # print("lon", lon)
    # print("alt", alt)
    # print("east", east)
    # print("north", north)

    also_save = []
    if hasattr(mesh, "mesh"):
        also_save.append("mesh")
    if hasattr(mesh, "comments"):
        also_save.append("comments")
    mesh.points.loc[:, ["x", "y", "z"]] = points
    mesh.to_file(back_transformed_ply, also_save=also_save)

    print("eastnorth_to_enu: Done")


def transformation_error_test(site_data_dir, in_ply, odp):

    if not os.path.isdir(odp):
        os.mkdir(odp)

    transformed_ply = os.path.join(odp, "plain_mesh_transformed.ply")
    back_transformed_ply = os.path.join(odp, "plain_mesh_back_transformed.ply")

    enu_to_eastnorth(site_data_dir, in_ply, transformed_ply)
    eastnorth_to_enu(site_data_dir, transformed_ply, back_transformed_ply)


if __name__ == "__main__":

    in_ply = "/path/to//MVS3D_mvs_mesh_evaluation/transformation_error/plain_mesh.ply"
    site_data_dir = "/path/to/VisSatDataset/site1-20201008T101440Z-001/site1"
    odp = "/path/to/MVS3D_mvs_mesh_evaluation/transformation_error"
    transformation_error_test(site_data_dir, in_ply, odp)

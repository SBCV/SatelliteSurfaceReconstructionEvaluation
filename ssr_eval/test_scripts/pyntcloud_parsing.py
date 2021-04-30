# https://pyntcloud.readthedocs.io/en/latest/PyntCloud.html
import filecmp
import numpy as np
from pyntcloud import PyntCloud
from ssr_eval.ext.vissat_toolset_lib.ply_np_converter import ply2np


def read_write_test(ifp, ofp):
    # https://github.com/daavoo/pyntcloud/blob/master/pyntcloud/core_class.py
    input_cloud = PyntCloud.from_file(ifp)
    output_cloud = PyntCloud(
        input_cloud.points,
        mesh=input_cloud.mesh,
        comments=input_cloud.comments,
    )
    output_cloud.to_file(ofp, also_save=["comments", "mesh"])
    assert filecmp.cmp(ifp, ofp)


def pytncloud_plyfile_test(ifp):
    cloud = PyntCloud.from_file(ifp)
    points_pyntcloud = cloud.points.loc[:, ["x", "y", "z"]].to_numpy()
    colors_pyntcloud = cloud.points.loc[:, ["red", "green", "blue"]].to_numpy()
    points_plyfile, colors_plyfile, comments = ply2np(ifp)
    assert np.array_equal(points_pyntcloud, points_plyfile)
    assert np.array_equal(colors_pyntcloud, colors_plyfile)


if __name__ == "__main__":

    ifp = "/path/to/ifp.ply"
    ofp = "/path/to/ofp.ply"

    pytncloud_plyfile_test(ifp)
    read_write_test(ifp, ofp)

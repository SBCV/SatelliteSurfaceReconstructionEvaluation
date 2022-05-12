import os


def _verify_odp_matches_data_idp(odp_site_prefix, site_data_idp):
    # site_data_idp: path/to/siteX
    # odp_site_prefix: MVS3D_site_X
    assert_msg = f"odp_site_prefix: {odp_site_prefix} vs. site_data_idp: {site_data_idp}"
    # Ensure the index of the dataset matches the index of the odp
    site_odp_index = odp_site_prefix[-1]
    site_data_index = site_data_idp[-1]
    assert site_odp_index in ["1", "2", "3"]
    assert site_data_index in ["1", "2", "3"]
    assert site_odp_index == site_data_index, assert_msg


def _verify_odp_matches_mesh_ifp(odp_site_prefix, mesh_ifp):
    # mesh_ifp: path/to/<MVS3D_site_X>_mvs/colmap/mvs/fused.ply
    # side_idp: path/to/<MVS3D_site_X>_mvs
    # mesh_dp: <MVS3D_site_X>
    site_idp = os.path.abspath(
        os.path.join(mesh_ifp, os.path.pardir, os.path.pardir, os.path.pardir)
    )
    mesh_dp = os.path.basename(os.path.dirname(site_idp))
    if not mesh_dp.startswith(odp_site_prefix):
        logger.vinfo("site_idp", site_idp)
        logger.vinfo("odp_site_prefix", odp_site_prefix)
        assert False


def _verify_odp_structure(odp, evaluation_suffix):
    assert_msg = (
        f"Incorrect suffix of {odp}, expected to end with: {evaluation_suffix}"
    )
    assert odp.endswith(evaluation_suffix), assert_msg


def verify_correct_output_name(site_data_idp, mesh_ifp, odp):
    # Expected input:
    #  site_data_idp: path/to/siteX
    #  mesh_ifp: path/to/<MVS3D_site_X>_mvs/colmap/mvs/fused.ply
    #  odp: path/to/<MVS3D_site_X>_evaluation
    evaluation_suffix = "_evaluation"
    odp_basename = os.path.basename(odp)
    odp_site_prefix = odp_basename.split(evaluation_suffix)[0]
    _verify_odp_structure(odp, evaluation_suffix)
    _verify_odp_matches_data_idp(odp_site_prefix, site_data_idp)
    _verify_odp_matches_mesh_ifp(odp_site_prefix, mesh_ifp)

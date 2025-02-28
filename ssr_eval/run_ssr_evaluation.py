import os
from shutil import copyfile
from enum import Enum
from ssr.utility.os_extension import mkdir_safely
from ssr.utility.logging_extension import logger
from ssr.meshlab_utility.meshlab import Meshlab

# Important: The "main_mesh" import MUST BE CALLED BEFORE "Pyntcloud", in order
# to properly execute "matplotlib.use('Agg')" in "main_mesh"
from ssr_eval.config.eval_config import EvalConfig
from ssr_eval.ssr_toolset.evaluate_ssr_surface import evaluate_mesh
from ssr_eval.utility.check_consistent_output_name import (
    verify_correct_output_name,
)
from pyntcloud import PyntCloud


SamplingMethods = Enum(
    "SamplingMethods", "vertex stratified_triangle montecarlo poisson_disk"
)


class Result:
    def __init__(self, name, median_err, completeness):
        self.name = name
        self.median_err = median_err
        self.completeness = completeness

    def __str__(self):
        return (
            f"name: {self.name} \n median_err: {self.median_err:.3f} \n"
            + f"completeness: {100 * self.completeness:.1f}"
        )


def create_config_from_template(config_template_ifp, config_fp):
    config_template_ifp = os.path.abspath(config_template_ifp)
    config_fp = os.path.abspath(config_fp)
    if not os.path.isfile(config_fp):
        logger.info(f"Config file {config_fp} not found")
        logger.info(
            f"Creating config file at {config_fp} from template {config_template_ifp}"
        )
        copyfile(config_template_ifp, config_fp)
        return True
    else:
        return False


def get_mesh_files(meshes_idp, algo_target_dn_list, mesh_target_fn):
    mesh_ifp_list = []
    if algo_target_dn_list is None:
        mesh_idp_list = os.listdir(meshes_idp)
    else:
        mesh_idp_list = []
        for algo_target_dn in algo_target_dn_list:
            mesh_idp_list.append(os.path.join(meshes_idp, algo_target_dn))
    for mesh_idp in mesh_idp_list:
        mesh_ifp = os.path.join(meshes_idp, mesh_idp, mesh_target_fn)
        assert os.path.isfile(mesh_ifp), f"Mesh file missing {mesh_ifp}"
        mesh_ifp_list.append(mesh_ifp)
    return mesh_ifp_list


def get_num_vertices_of_ply(ifp):
    point_cloud = PyntCloud.from_file(ifp)
    points = point_cloud.points.loc[:, ["x", "y", "z"]].to_numpy()
    num_vertices = points.shape[0]
    return num_vertices


if __name__ == "__main__":

    ssr_eval_config_template_ifp = "./configs/eval_template.toml"
    ssr_eval_config_fp = "./configs/eval.toml"
    if create_config_from_template(
        ssr_eval_config_template_ifp, ssr_eval_config_fp
    ):
        abort_msg = "Adjust the values in the (newly created) config file and run the pipeline again!"
        logger.info(abort_msg)
        assert False, abort_msg
    ssr_eval_config = EvalConfig.get_from_file(ssr_eval_config_fp)

    fill_small_holes = ssr_eval_config.fill_small_holes
    sampling_method = SamplingMethods[ssr_eval_config.sampling_method]
    # assert sampling_method in list(map(str, SamplingMethods))

    mesh_ifp_list = get_mesh_files(
        meshes_idp=ssr_eval_config.meshes_idp,
        algo_target_dn_list=ssr_eval_config.algo_target_dn_list,
        mesh_target_fn=ssr_eval_config.mesh_target_fn,
    )

    sample_vertices = sampling_method != SamplingMethods.vertex
    if sample_vertices:
        vissat_fused_ifp = ssr_eval_config.vissat_fused_ifp
        logger.vinfo("vissat_fused_ifp", vissat_fused_ifp)
        vissat_fused_num_vertices = get_num_vertices_of_ply(vissat_fused_ifp)
        logger.vinfo("vissat_fused_num_vertices", vissat_fused_num_vertices)
    else:
        vissat_fused_num_vertices = None

    res_tripplets = []
    vissat_dataset_site_idp = ssr_eval_config.vissat_dataset_site_idp
    odp = ssr_eval_config.odp
    mkdir_safely(odp)
    meshlab = Meshlab(
        executable_fp=ssr_eval_config.meshlab_server_fp,
        meshlab_temp_dp=ssr_eval_config.meshlab_temp_dp,
    )
    for mesh_ifp in mesh_ifp_list:

        if ssr_eval_config.check_output_name_correctness:
            verify_correct_output_name(vissat_dataset_site_idp, mesh_ifp, odp)
        sampling_method_str = sampling_method.name
        odn = os.path.basename(os.path.dirname(mesh_ifp))
        specific_suffix = f"_sm_{sampling_method_str}"
        if fill_small_holes:
            specific_suffix += "_hf"
        specific_odp = os.path.join(odp, odn + specific_suffix)
        assert_msg = f"Directory already exists: {specific_odp}"
        assert not os.path.isdir(specific_odp), assert_msg
        os.mkdir(specific_odp)

        if sample_vertices:
            stem, ext = os.path.splitext(os.path.basename(mesh_ifp))
            sampled_point_cloud_fp = os.path.join(
                specific_odp, f"{stem}{specific_suffix}{ext}"
            )
            logger.vinfo("sampled_point_cloud_fp", sampled_point_cloud_fp)

            # Use for each mesh the same number of samples
            # (i.e. the number of points in fused.ply)
            meshlab.sample_mesh(
                mesh_ifp,
                sampled_point_cloud_fp,
                vissat_fused_num_vertices,
                sampling_method.name,
            )
        else:
            sampled_point_cloud_fp = mesh_ifp

        median_err, completeness = evaluate_mesh(
            site_data_dir=vissat_dataset_site_idp,
            in_ply=sampled_point_cloud_fp,
            out_dir=specific_odp,
            fill_small_holes=fill_small_holes,
            max_processes=16,
            write_mesh=False,
        )

        logger.info("---------------------------------------------")
        logger.vinfo("mesh_ifp", mesh_ifp)
        logger.vinfo("fill_small_holes", fill_small_holes)
        logger.vinfo("odp", specific_odp)
        logger.vinfo("sampled_point_cloud_fp", sampled_point_cloud_fp)
        logger.vinfo("median_err", f"{median_err:.3f}")
        logger.vinfo("completeness", f"{100 * completeness:.1f}")
        logger.info("---------------------------------------------")
        res_tripplets.append(
            Result(
                name=os.path.basename(os.path.dirname(mesh_ifp)),
                median_err=median_err,
                completeness=completeness,
            )
        )

    for res in res_tripplets:
        print(res)

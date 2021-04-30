import os
from shutil import copyfile
from enum import Enum
from ssr.config.ssr_config import SSRConfig
from ssr.utility.os_extension import mkdir_safely
from ssr.utility.logging_extension import logger
from ssr.meshlab_utility.meshlab import Meshlab

# Important: The "main_mesh" import MUST BE CALLED BEFORE "Pyntcloud", in order
# to properly execute "matplotlib.use('Agg')" in "main_mesh"
from ssr_eval.ssr_toolset.evaluate_ssr_surface import evaluate_mesh
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


def check_correct_input_output(site_data_idp, mesh_ifp, odp):
    site_odp_prefix = os.path.basename(odp).split("_evaluation")[0]
    assert_msg = f"{site_odp_prefix} vs. {site_data_idp}"
    assert site_odp_prefix[-1] == site_data_idp[-1], assert_msg
    site_idp = os.path.abspath(
        os.path.join(mesh_ifp, os.path.pardir, os.path.pardir, os.path.pardir)
    )
    mesh_dp = os.path.basename(os.path.dirname(site_idp))
    if not mesh_dp.startswith(site_odp_prefix):
        logger.vinfo("site_idp", site_idp)
        logger.vinfo("site_odp_prefix", site_odp_prefix)
        assert False


def get_num_vertices_of_ply(ifp):
    point_cloud = PyntCloud.from_file(ifp)
    points = point_cloud.points.loc[:, ["x", "y", "z"]].to_numpy()
    num_vertices = points.shape[0]
    return num_vertices


if __name__ == "__main__":

    ssr_eval_config_template_ifp = "./configs/eval_template.cfg"
    ssr_eval_config_fp = "./configs/eval.cfg"
    if create_config_from_template(
        ssr_eval_config_template_ifp, ssr_eval_config_fp
    ):
        abort_msg = "Adjust the values in the (newly created) config file and run the pipeline again!"
        logger.info(abort_msg)
        assert False, abort_msg
    ssr_eval_config = SSRConfig(config_fp=ssr_eval_config_fp)
    SSRConfig.set_instance(ssr_eval_config)

    fill_small_holes = ssr_eval_config.get_option_value(
        "fill_small_holes", bool
    )

    sampling_method_str = ssr_eval_config.get_option_value(
        "sampling_method", str
    )
    sampling_method = SamplingMethods[sampling_method_str]
    # assert sampling_method in list(map(str, SamplingMethods))

    meshes_idp = ssr_eval_config.get_option_value("meshes_idp", str)
    algo_target_dn_list = ssr_eval_config.get_option_value(
        "algo_target_dn_list", list
    )
    mesh_target_fn = ssr_eval_config.get_option_value("mesh_target_fn", str)
    mesh_ifp_list = get_mesh_files(
        meshes_idp=meshes_idp,
        algo_target_dn_list=algo_target_dn_list,
        mesh_target_fn=mesh_target_fn,
    )

    sample_vertices = sampling_method != SamplingMethods.vertex
    if sample_vertices:
        vissat_fused_ifp = ssr_eval_config.get_option_value(
            "vissat_fused_ifp", str
        )
        logger.vinfo("vissat_fused_ifp", vissat_fused_ifp)
        vissat_fused_num_vertices = get_num_vertices_of_ply(vissat_fused_ifp)
        logger.vinfo("vissat_fused_num_vertices", vissat_fused_num_vertices)
    else:
        vissat_fused_num_vertices = None

    res_tripplets = []
    vissat_dataset_site_idp = ssr_eval_config.get_option_value(
        "vissat_dataset_site_idp", str
    )
    odp = ssr_eval_config.get_option_value("odp", str)
    mkdir_safely(odp)
    meshlab = Meshlab()
    for mesh_ifp in mesh_ifp_list:

        check_correct_input_output(vissat_dataset_site_idp, mesh_ifp, odp)
        sampling_method_str = sampling_method.name
        odn = os.path.basename(os.path.dirname(mesh_ifp))
        specific_suffix = f"_sm_{sampling_method_str}"
        if fill_small_holes:
            specific_suffix += "_hf"
        specific_odp = os.path.join(odp, odn + specific_suffix)
        assert_msg = f"Directory {specific_odp} already exists"
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

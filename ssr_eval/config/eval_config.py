import toml
from pydantic import BaseModel
from typing import List, Dict, Union


class EvalConfig(BaseModel):

    meshlab_server_fp: str
    meshlab_temp_dp: str

    fill_small_holes: Union[bool, int]
    sampling_method: str
    meshes_idp: str
    algo_target_dn_list: List[str]

    mesh_target_fn: str
    vissat_fused_ifp: str
    vissat_dataset_site_idp: str
    odp: str

    check_output_name_correctness: Union[bool, int] = 1

    @classmethod
    def get_from_file(cls, toml_ifp):
        config_dict = toml.load(toml_ifp)
        return cls(**config_dict)

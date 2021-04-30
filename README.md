# SatelliteSurfaceReconstructionEvaluation
3D Surface Reconstruction From Multi-Date Satellite Images Evaluation 

## Installation

- Requirements
    - Install and configure [SatelliteSurfaceReconstruction](https://github.com/SBCV/SatelliteSurfaceReconstruction)
        - Including the python libraries defined in ```SatelliteSurfaceReconstruction/requirements.txt```
        - Including Meshlab
    - Install Pyntcloud by running ```pip install -r requirements.txt```
- ```git clone https://github.com/SBCV/SatelliteSurfaceReconstructionEvaluation.git```

## Configure the SatelliteSurfaceReconstructionEvaluation Project
- Add ```SatelliteSurfaceReconstruction``` to the ```SatelliteSurfaceReconstructionEvaluation``` project
    - For example in Pycharm
        - Open ```SatelliteSurfaceReconstructionEvaluation```
        - Open ```SatelliteSurfaceReconstruction``` and attach it to ```SatelliteSurfaceReconstructionEvaluation```
        - Go to File / Settings / Project: ```SatelliteSurfaceReconstructionEvaluation``` / Project Dependencies
            - Select ```SatelliteSurfaceReconstructionEvaluation```
            - Make sure that ```SatelliteSurfaceReconstructionEvaluation``` is selected

## Run the Evaluation Pipeline
- Run ```ssr_eval/run_ssr_evaluation.py```
- The first time ```ssr_eval/run_ssr_evaluation.py``` is executed, it will create a configuration at ```ssr_eval/configs/eval.cfg``` using the template located at ```ssr_eval/configs/eval_template.cfg```
- Adjust the paths in the config file ```ssr_eval/configs/eval.cfg``` such as
    - ```meshlab_server_fp```
    - ```meshlab_temp_dp```
- Select the required parameters such as 
    - ```sampling_method```
    - ```algo_target_dn_list```
    - ```vissat_dataset_site_idp```
    - ...
- Run ```ssr_eval/run_ssr_evaluation.py```
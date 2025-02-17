from numba import config
config.DISABLE_JIT = True

import spatialdata as sd
from spatialdata.transformations.transformations import Identity
from spatialdata.transformations import set_transformation
from spatialdata.models import PointsModel
import dask.array as da
import numpy as np
import fire 
import os
import tifffile as tif
import pandas as pd
import exp_metadata_json as exp_meta

sdata = sd.SpatialData()

def to_spatialdata_qc(experiment_metadata_json, *spotsPath_imgPaths):

    ExpJsonParser = exp_meta.ExpJsonParser(experiment_metadata_json)

    try:
        desired_genes = ExpJsonParser.meta["desired_genes"]
    except:
        desired_genes = []

    dapis_after = []
    for file in spotsPath_imgPaths:
        file_name = file
        if file_name.startswith('registered_') and (file_name.endswith('_DAPI.tiff') or file_name.endswith('_DAPI.tif')): 
            dapis_after.append(file)
        if file_name.startswith('norm_') and (file_name.endswith('_nuclei.tiff') or file_name.endswith('_nuclei.tif')):
            nuclei_dir_after = file
        if file_name.endswith('.csv'):
            spots_path = file

    # spots_filtered = spots[(spots.passes_thresholds_postcode == True) & (spots.target_postcode == gene_name) & (spots.Probability>.7)].reset_index(drop=True)
    spots = pd.read_csv(spots_path)
    spots_filtered = spots[(spots.passes_thresholds_postcode == True) & (spots.Probability>.7)].reset_index(drop=True)
    
    points = PointsModel.parse(
        spots_filtered,
        coordinates={"x": "xc", "y": "yc"},
        feature_key="target_postcode",
        transformations={"global": Identity()},
    )
    sdata["transcripts"] = points

    ref_after = tif.memmap(nuclei_dir_after)

    da_arr = da.array(ref_after)#.astype(np.uint8)
    arr = np.expand_dims(da_arr, axis=0)
    sd_image = sd.models.Image2DModel.parse(
                        arr,
                        dims=("c", "y", "x"),
                        # scale_factors=[2, 2, 2],
                        chunks=(1, 2048, 2048),
                    )
    set_transformation(
                sd_image, Identity(), to_coordinate_system="global"
            ) 
    sdata.images["org_dapi_img"] = sd_image

    for img in dapis_after:
        dapi_img = tif.imread(img)
        da_arr = da.array(dapi_img)#.astype(np.uint8)
        arr = np.expand_dims(da_arr, axis=0)
        sd_image = sd.models.Image2DModel.parse(
                            arr,
                            # scale_factors=[2, 2, 2],
                            dims=("c", "y", "x"),
                            chunks=(1, 2048, 2048),
                        )
        set_transformation(
                    sd_image, Identity(), to_coordinate_system="global"
                ) 
        r = img.split("_")[1]
        sdata.images[f"reg_dapi_{r}_img"] = sd_image

    if desired_genes is not None: 

        try:
            for gene_name in desired_genes:
                spots_filtered = spots[(spots.passes_thresholds_postcode == True) & (spots.target_postcode == gene_name) & (spots.Probability>.7)].reset_index(drop=True)
                points = PointsModel.parse(
                    spots_filtered,
                    coordinates={"x": "xc", "y": "yc"},
                    feature_key="target_postcode",
                    transformations={"global": Identity()},
                )
                sdata[gene_name] = points
        except: pass

    output_path = os.path.join(os.getcwd(), "spatialdata_processed")
    sdata.write(output_path, overwrite=False, consolidate_metadata=True)



if __name__ == "__main__":
    cli = {
        "to_spatialdata": to_spatialdata_qc
    }
    fire.Fire(cli)

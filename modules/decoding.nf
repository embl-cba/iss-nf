pythonScript = "${workflow.projectDir}/bin/decoder_starfish.py"

process SPOT_FINDER {

    input:
    path('*')
    val(fov_id)
    val(threshold)
    //file coordinates from params.imageDir

    output:
    path("*.npy")
    path ("*.csv")
    val(threshold)

    script:
    """
    python ${pythonScript} decode_fov ./ ${fov_id} ${threshold}
    """
   }
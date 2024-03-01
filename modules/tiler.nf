pythonScript = "${workflow.projectDir}/bin/tiler.py"

process TILING {
    publishDir "Tiled", mode: 'copy', overwrite: true
    debug true
    label 'small'

    input:
    tuple val(sampleID), path(transformedImage), val(tile_size)

    output:
    tuple val(sampleID), path("*.tiff")
    tuple val(sampleID), path("*.csv")

    script:
    """
    python ${pythonScript} run_tiling $transformedImage $tile_size
    """
}

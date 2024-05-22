pythonScript = "${workflow.projectDir}/bin/threshold_finder.py"

process THRESHOLD_FINDER {

    debug true
    
    input:
    path(starfish_tables)

    output:
    path('picked_threshold.txt')
    path("4-thresh_qc.html")
    
    script:
    """
    python ${pythonScript} autocompute_thr ${params.n_gene_panel} ${params.empty_barcodes} ${params.remove_genes} ${params.invalid_codes} $starfish_tables 
    """
}
import numpy as np
import pandas as pd
# import fire
import matplotlib.pyplot as plt
import os
import base64
import sys
import json

def plot_report(thresholds, false_discovery_rates, decoded_spots, picked_threshold):

    data = {'number_of_decoded': decoded_spots,
            'thresholds': thresholds,
            'fdrs': false_discovery_rates}
    plt.figure(figsize=(10, 8))

    sc = plt.scatter(thresholds, false_discovery_rates, c=decoded_spots,
                    cmap='viridis', s=np.array(data['number_of_decoded'])*.01)

    cbar = plt.colorbar(sc)
    cbar.set_label('Number of Decoded')

    plt.title('Scatter Plot of Thresholds vs. FDRs Colored by Number of Decoded')
    plt.xlabel('Thresholds')
    plt.ylabel('FDRs')
    plt.xscale('log')
    plt.axvline(x=picked_threshold, color='r', ls='--', label=f'Picked threshold - {picked_threshold}')
    plt.legend()
    qc_path = os.getcwd()
    output_plot_path = os.path.join(qc_path, "picked_thresh_plot.png")
    plt.savefig(output_plot_path, bbox_inches='tight')
    plt.show()
    plt.close() 

    with open(output_plot_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    html_content = f"""
    <html>
    <head>
    <title>QC Plot</title>
    </head>
    <body>
    <h1>QC Plot</h1>
    <p>This plot shows how the threshold is chosen based on the number of decoded vs FDR for all three chosen tiles.</p>
    <img src="data:image/png;base64,{encoded_string}" alt="QC Plot">
    </body>
    </html>
    """
    output_html_path = os.path.join(qc_path, "4-thresh_qc.html")
    with open(output_html_path, 'w') as f:
        f.write(html_content)

def select_best_threshold1(thresholds, detected_spots, decoded_spots, false_discovery_rates):

    best_fdr = float('inf')
    best_threshold = None

    for i, threshold in enumerate(thresholds):
        fdr = false_discovery_rates[i]

        if fdr < best_fdr:
            best_fdr = fdr
            best_threshold = threshold
        elif fdr == best_fdr:
            if decoded_spots[i] > decoded_spots[i]:
                best_threshold = threshold
            elif decoded_spots[i] == decoded_spots[i]:
                if detected_spots[i] > detected_spots[i]:
                    best_threshold = threshold

    return best_threshold


def select_best_threshold2(thresholds, detected_spots, decoded_spots, false_discovery_rates):

    best_score = float('-inf')
    best_threshold = None

    for i, threshold in enumerate(thresholds):
        score = -(2 * false_discovery_rates[i]**3) + (2*decoded_spots[i])

        if score > best_score:
            best_score = score
            best_threshold = threshold

    return best_threshold


def select_best_threshold3(thresholds, detected_spots, decoded_spots, false_discovery_rates):

    best_score = float('-inf')
    best_threshold = None

    for i, threshold in enumerate(thresholds):

        score = (decoded_spots[i]) - (false_discovery_rates[i] **3)

        if score > best_score:
            best_score = score
            best_threshold = threshold

    return best_threshold


def mode_first(data):
    
    frequency = {}
    for item in data:
        frequency[item] = frequency.get(item, 0) + 1
    
    max_frequency = max(frequency.values())
    modes = [key for key, value in frequency.items() if value == max_frequency]
    
    return modes[0] if modes else None


def get_fdr(empties, total, n_genesPanel, empty_barcodes, remove_genes):

    empty_n = len(empty_barcodes)
    if remove_genes is not None: 
        panel_n = (n_genesPanel - len(remove_genes) + empty_n)
    else:
        panel_n = (n_genesPanel + empty_n)
    
    return (empties / total) * (panel_n / empty_n)

def auto_threshold(n_genesPanel, empty_barcodes, remove_genes, invalid_codes, *args):
        
        empty_barcodes = json.load(open(empty_barcodes, 'r'))
        remove_genes   = json.load(open(remove_genes, 'r'))
        invalid_codes  = json.load(open(invalid_codes, 'r')) 

        df_general = pd.DataFrame(columns=['threshold', '#Detected', '#Decoded', 'Percent', 'FDR', 'Picked_thresh'])

        for path in args:
            print(path, '-----------------------------------------')
            components = path.split('/')
            filename = components[-1]
            fov_name = filename.split('-')[0]
            last_part = filename.split('-')[-1]
            threshold = float(last_part[:-4])

            df = pd.read_csv(path)

            filtered_df = df[df['passes_thresholds']==True]
            filtered_df = filtered_df[~filtered_df['target'].isin(empty_barcodes)]
            filtered_df = filtered_df[~filtered_df['target'].isin(remove_genes)]
            filtered_df = filtered_df[~filtered_df['target'].isin(invalid_codes)]

            total_filtered_count = len(filtered_df)
            empty_barcodes_count = df[df['target'].isin(empty_barcodes)].shape[0]
            invalid_codes_count = df[df['target'].isin(invalid_codes)].shape[0]

            df_general = df_general.append({'threshold': threshold,
                        '#Detected': len(df),
                        '#Decoded': total_filtered_count,
                        'Percent': total_filtered_count/len(df) * 100,
                        'FDR': get_fdr(empty_barcodes_count, len(df), n_genesPanel, empty_barcodes, remove_genes)}, ignore_index=True)
        
        thresholds = df_general['threshold']
        detected_spots = df_general['#Detected']
        decoded_spots = df_general['#Decoded']
        false_discovery_rates = df_general['FDR']

        arr = [
            select_best_threshold1(thresholds, detected_spots, decoded_spots, false_discovery_rates),
            select_best_threshold2(thresholds, detected_spots, decoded_spots, false_discovery_rates),
            select_best_threshold3(thresholds, detected_spots, decoded_spots, false_discovery_rates),
        ]

        picked_threshold = mode_first(arr)
        plot_report(thresholds, false_discovery_rates, decoded_spots, picked_threshold)

        with open('picked_threshold.txt', 'w') as file:
                file.write(str(picked_threshold))
        
    
if __name__ == "__main__":
    
    n_genesPanel = int(sys.argv[1])
    empty_barcodes = (sys.argv[2])
    remove_genes = (sys.argv[3])
    invalid_codes = (sys.argv[4])
    csv_paths = (sys.argv[5])
    auto_threshold(n_genesPanel, empty_barcodes, remove_genes, invalid_codes, csv_paths)
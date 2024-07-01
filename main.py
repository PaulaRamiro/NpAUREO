import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


def read_and_transform_csv(directory):
    """
    Lee todos los archivos CSV en un directorio y los combina en un solo DataFrame.

    :param directory: Ruta al directorio que contiene los archivos CSV.
    :return: DataFrame combinado.
    """
    # Obtener la lista de todos los archivos CSV en el directorio
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    # Leer archivo CSV y convertir en DataFrames
    for file in csv_files:
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path, sep='\t')

    # Multiple_replicons to bool column
    df.loc[df['Multiple_replicons'] == 'Multiple replicons', 'Multiple_replicons'] = True
    df.loc[df['Multiple_replicons'] == 'Single replicons', 'Multiple_replicons'] = False

    # Filter undetected plasmids
    df = df[df['rep_type.s.'] != '-']

    df_og = df.copy()
    df_og = df_og.rename(columns={'rep_type.s.': 'plasmids'})

    # Filter only those plasmids which appear ar least 3 different times
    conteo = df_og.groupby('plasmids')['PCN'].count().reset_index()
    repes = list(conteo[conteo['PCN'] >= 3]['plasmids'])
    df_filtered = df_og[df_og['plasmids'].isin(repes)]
    df_filtered['plasmids'] = df_filtered['plasmids'].str.split(',')

    # Create a dictionary where each key is a possible combination of plasmid replicons and each value is a dataframe
    # containing every element of the key, separated or combined
    df_cross = pd.DataFrame(columns=df_filtered.columns)
    df_cross['replicon_ID'] = pd.Series(dtype='str')
    for i in repes:
        df_loop = df_filtered.copy()
        df_loop['plasmids'] = df_loop['plasmids'].str.join(',')
        comb = df_loop[df_loop['plasmids'] == i]
        if ',' in i:
            single = df_loop[(df_loop['plasmids'] == i) & (df_loop['Multiple_replicons'] == False)]
            i = i.split(',')
            for j in i:
                single = pd.concat([single, df_loop[df_loop['plasmids'] == j]])
            comb = pd.concat([comb, single])
            i = ','.join(i)
        comb['replicon_ID'] = i
        df_cross = pd.concat([df_cross, comb])

    return df_cross


def main():
    # Directorio donde se encuentran los archivos CSV
    csv_directory = 'src'

    # Leer y combinar los archivos CSV
    combined_df = read_and_transform_csv(csv_directory)

    # Guardar el DataFrame combinado en un nuevo archivo CSV
    output_path = os.path.join(csv_directory, 'Plasmid_interactions_combined.csv')
    combined_df.to_csv(output_path, index=False)

    print(f'Todos los archivos CSV han sido combinados en {output_path}')


if __name__ == "__main__":
    main()

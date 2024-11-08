
![WorkflowNumeroPaureo](https://github.com/user-attachments/assets/2bd1d2c5-85e0-40d7-a9ea-f36bd78b2d96)




## **Download data** 

First, we downloaded the metadata table from NCBI:

```diff

+ # bash #

# Both databases were used indistinctly, selecting for each genus, the one that contained most samples of our interest

wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt 
wget https://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt

```
Samples were selected by filtering the desired genus and "Complete Genome". For example:

```diff
+ # bash #

grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt
```

Then, we used **Entrez Direct** (https://www.ncbi.nlm.nih.gov/books/NBK179288/) to download the genome assemblies through esearch, with the following arguments:

```diff

+ # bash #

esearch -db assembly -query "biosample" | efetch -format fasta > biosample.fasta

```

And we analyze the number of contigs of each assembly file to filter out those that don't contain plasmids:


```diff

+ # bash #

mkdir LengthAssembly
for file in *.fasta *.fna; do
    awk '/^>/{if (l!="") print l; print; l=0; next}{l+=length($0)}END{print l}' "$file" > "LengthAssembly/$(basename -- "$file" .fna)"
done

+ # Python3 #

import os
current_directory = os.getcwd()

# Create a dictionary to store modified lines
modified_lines = {}

# Modify files
for filename in os.listdir(current_directory):
    if not filename.startswith('MOD_'):
        output_filename = f"MOD_{filename}"
        file_name = os.path.splitext(filename)[0]
        
        with open(filename, 'r') as file:
            with open(output_filename, 'w') as output_file:
                output_file.write("Biosample,contig,sample,length\n")
                for line in file:
                    if line.startswith(">"):
                        parts = line.strip().split(' ', 1)
                        if len(parts) == 2:
                            sample_info = f"{file_name},{parts[0]},{parts[1].rstrip()}"
                            number_line = next(file).strip()
                            output_file.write(f"{sample_info},{number_line}\n")
                            modified_lines[sample_info] = number_line

# Merge modified lines into 'alllengths.txt'
with open('alllengths.txt', 'w') as merged_file:
    merged_file.write("Biosample,contig,sample,length\n")
    for sample_info, number_line in modified_lines.items():
        merged_file.write(f"{sample_info},{number_line}\n")
```

Then, we downloaded the files containing run information for selected assemblies of NCBI, also with esearch: 

```diff

+ # bash #

esearch -db sra -query Biosample | efetch -format runinfo > Biosample.numbers
```

With the Biosample.numbers files, we filter those runs paired-end with "genomic" as a library source and from the platform Illumina, and use the run IDs to download the reads with fasterq-dump from **SRA-toolkit** package (https://hpc.nih.gov/apps/sratoolkit.html):

```diff
+ # Python3 #

import multiprocessing
import subprocess

with open('DefNumbers.txt', 'r') as file:    numbers = [(line.strip()) for line in file if line.strip()]

def execute_fasterq_dump(number):
    command = f"fasterq-dump --split-3 {number}"
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Command executed for number: {number}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command for number {number}: {e}")

if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=8)     # This step sets the number of cores to be used to parallelize, in this case, 8. Tune this to fit your machine.
    pool.map(execute_fasterq_dump, numbers)
    pool.close()
    pool.join()

```

## **Extract coverage information** 


Once the reads and assembly files have been downloaded, we ran **CoverM** (https://github.com/wwood/CoverM) to extract the coverage information, by using the following flags:

```diff
+ # bash #

coverm contig --output-file Biosample -m trimmed_mean -r Biosample.fasta -1 reads_1.fastq -2 reads_2.fastq

```

Once finished. We parse the results with this custom code:

```diff
+ # bash #

header_printed=false

for file in *; do
    if [ -f "$file" ]; then
        if [ "$header_printed" = false ]; then
            awk 'BEGIN {print "Filename\tContent"} NR>1 {print FILENAME "\t" $0}' "$file" > "temp_$file"
            header_printed=true
        else
            awk 'NR>1 {print FILENAME "\t" $0}' "$file" > "temp_$file"
        fi
    fi
done
cat temp_* > combined_file.txt
rm temp_*
```


## **Extract plasmid information** 

First, we extracted the Plasmid Taxonomic Units (PTUs) information of each cluster with **COPLA** (https://github.com/santirdnd/COPLA), using the following arguments: 

```diff
+ # python #
python3 bin/copla.py "$fasta_file" \
        databases/Copla_RS84/RS84f_sHSBM.pickle \
        databases/Copla_RS84/CoplaDB.fofn \
        "$fasta_file"_output

```

We also run **mob_suite** (https://github.com/phac-nml/mob-suite) on the assemblies, to extract replicon type information. We run it by paralellizing with the following command:

```diff
+ # bash #

mkdir Results_mobtyper
ls *.fasta | xargs -n 1 -P 8 -I {} sh -c 'mob_typer --multi --infile "{}" --out_file "Results_mobtyper/{}"'

```
And parse the results using the code:

```diff

+ # bash #
for f in *.fasta; do awk -v fName="${f%.fasta}" '{printf("%s,%s\n", (FNR==1 ? "filename" : fName), $0)}' "$f" > mod"$f"; done
cat mod* > all_results.txt

```
**Plasmidfinder** (https://bitbucket.org/genomicepidemiology/plasmidfinder/src/master/)  was also run on all plasmids with the following options:
```diff

+ # bash #
for file in *.fasta; do mkdir outputs/${file}; plasmidfinder.py -i ${file} -o outputs/${file} -p PlasmidfinderDB/plasmidfinder_db -x; done

```
Results were parsed with the following custom python script:

```diff
import os
import pandas as pd

# Get the current directory
current_dir = os.getcwd()

# Initialize an empty list to store dataframes
dfs = []

# Iterate over each folder in the current directory
for folder_name in os.listdir(current_dir):
    folder_dir = os.path.join(current_dir, folder_name)
    
    # Check if the folder contains the results.tsv file
    if os.path.isfile(os.path.join(folder_dir, "results_tab.tsv")):
        # Read the results.tsv file into a pandas dataframe
        df = pd.read_csv(os.path.join(folder_dir, "results_tab.tsv"), delimiter='\t')
        
        # Add a new column with the folder name
        df.insert(0, "Folder", folder_name)
        
        # Append the dataframe to the list
        dfs.append(df)

# Concatenate all dataframes into one
merged_df = pd.concat(dfs, ignore_index=True)

# Save the merged dataframe to a new file in the current directory
merged_df.to_csv(os.path.join(current_dir, "merged_results.tsv"), sep='\t', index=False)
 
```

## **Extract plasmids with RNAI** 

In annotation files (.gff), we searched for those plasmids with replication through the RNAI-RNAII regulation system.  

```diff
+ # bash #

grep "RNAI;" *.gff > Files_with_RNAI.txt
sed 's/.gff3:contig_1//' Files_with_RNAI.txt > Files_with_RNAI_2.txt

```


![Pipeline_NumeroPaureo](https://github.com/PaulaRamiro/NpAUREO/assets/152322543/9e499fa8-4bfa-41fa-bc3a-80bb0601debb)


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

grep "Genus" assembly_summary_genbank.txt | grep "Complete Genome" > data_Genus.txt

```

Then, we used **esearch v20.6** (https://www.ncbi.nlm.nih.gov/books/NBK179288/) to download the genome assemblies, with the following arguments:

```diff

+ # bash #

esearch -db ${assembly} -query "${biosample}" | efetch -format fasta > ${biosample}.fasta

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

esearch -db sra -query ${Biosample} | efetch -format runinfo > ${Biosample}.numbers

```

With the ${Biosample}.numbers files, we filter those runs paired-end with "genomic" as a library source, and use the run IDs to download the reads with fasterq-dump from **SRA-toolkit** package (https://hpc.nih.gov/apps/sratoolkit.html):

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


Once the reads and assembly files have been downloaded, we ran **CoverM v0.6.1** (https://github.com/wwood/CoverM) to extract the coverage information by using the following flags:

```diff
+ # bash #

coverm contig --output-file ${Biosample} -m trimmed_mean -r ${Biosample}.fasta -1 reads_1.fastq -2 reads_2.fastq

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

First, we extracted the Plasmid Taxonomic Units (PTUs) information of each cluster with **COPLA v1.0** (https://github.com/santirdnd/COPLA), using the following arguments: 

```diff
+ # python #
python3 bin/copla.py "$fasta_file" \
        databases/Copla_RS84/RS84f_sHSBM.pickle \
        databases/Copla_RS84/CoplaDB.fofn \
        "$fasta_file"_output

```

We also run **mob_suite v3.1.8** (https://github.com/phac-nml/mob-suite) on the assemblies to extract replicon-type information. We run it by parallelizing with the following command:

```diff
+ # bash #

mkdir Results_mobtyper
ls ${Biosample}.fasta | xargs -n 1 -P 8 -I {} sh -c 'mob_typer --multi --infile "{}" --out_file "Results_mobtyper/{}"'

```
And parse the results using the code:

```diff

+ # bash #
for f in ${Biosample}.fasta; do awk -v fName="${f%.fasta}" '{printf("%s,%s\n", (FNR==1 ? "filename" : fName), $0)}' "$f" > mod"$f"; done
cat mod* > mobtyper_results.txt

```

## **Extract antibiotic resistance information** 

We run **abricate v1.0.1** (https://github.com/tseemann/abricate) on the assemblies to analyze the resistance gene content of each plasmid by using the following command:

```diff
+ # bash #
abricate ${Biosample}.fasta > AbricateResults.tab

```


<img width="682" alt="Captura de pantalla 2024-03-10 a las 15 34 32" src="https://github.com/PaulaRamiro/NpAUREO/assets/152322543/0f71a2df-2fed-4d96-aa3b-a6ffb1b3b477">

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

Then, we used esearch to download the genome assemblies with the following arguments:

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

With the Biosample.numbers files, we use the run IDs to download the reads with fasterq-dump from samtools package:

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


Once the reads and assembly files have been downloaded, we ran **CoverM** to extract the coverage information, by using the following flags:

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

First, we divide plasmids in clusters with mge-cluster (), using the following arguments:

```diff
+ # bash #


```
Once we classified the plasmids into clusters, we extracted the PTU information of each cluster with COPLA (), using the following arguments: 

```diff
+ # bash #


```

We also run mobtyper on our .fasta files by paralellizing with the following command:

```diff
+ # bash #

mkdir Results_mobtyper
ls *.fasta *.fna | xargs -n 1 -P 8 -I {} sh -c 'mob_typer --multi --infile "{}" --out_file "Results_mobtyper/{}"'

```
And parse the results using the code:

```diff

+ # bash #
for f in *.fasta; do awk -v fName="${f%.fasta}" '{printf("%s,%s\n", (FNR==1 ? "filename" : fName), $0)}' "$f" > mod"$f"; done
cat mod* > all_results.txt

```






![WorkflowNumeroPaureo](https://github.com/user-attachments/assets/2bd1d2c5-85e0-40d7-a9ea-f36bd78b2d96)




## **Download data** 

First, we downloaded the metadata table from NCBI:

```diff

+ # bash #

# Both databases were used indistinctly, selecting for each genus, the one that contained most samples of our interest

# For Linux users:
wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt
wget https://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt

#For MacOS users:
curl -O https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt
curl -O https://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt

```
Samples were selected by filtering the desired genus and "Complete Genome". For example:

```diff

+ # bash #

grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt

```

Then, we used **Entrez Direct** (v20.6) (https://www.ncbi.nlm.nih.gov/books/NBK179288/) to download the genome assemblies, with the following arguments:


```diff

+ # bash #

# For Linux users:
esearch -db assembly -query "biosample_ID" \
    | esummary \
    | xtract -pattern DocumentSummary -element FtpPath_GenBank \
    | while read -r line ;
    do
        fname=$(echo $line | grep -o 'GCA_.*' | sed 's/$/_genomic.fna.gz/') ;
        wget "$line/$fname" ;
    done

# For MacOS users:
esearch -db assembly -query "biosample_ID" \
    | esummary \
    | xtract -pattern DocumentSummary -element FtpPath_GenBank \
    | while read -r line ;
    do
        fname=$(echo $line | grep -o 'GCA_.*' | sed 's/$/_genomic.fna.gz/') ;
        curl -O "$line/$fname" ;
    done

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

With the Biosample.numbers files, we filter those runs paired-end with "genomic" as a library source and from the platform Illumina, and use the run IDs to download the reads with fasterq-dump from **SRA-toolkit** package (v2.11.3)(https://hpc.nih.gov/apps/sratoolkit.html):

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
We checked the topology of the plasmids to maintain only those that were circular with the following script that connects to the NCBI API: 

```diff
+ # Python3 #
import requests
from xml.etree import ElementTree
import time
from urllib3.exceptions import MaxRetryError  

def get_contig_topology(contig_id, max_retries=100, backoff_factor=1):
  """Fetches contig topology with retry logic.

  Args:
      contig_id (str): The ID of the contig to fetch.
      max_retries (int, optional): The maximum number of retries before giving up. Defaults to 5.
      backoff_factor (float, optional): The factor by which to increase the sleep time between retries. Defaults to 1.

  Returns:
      str: The topology of the contig, or None if all retries fail.
  """
  url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
  params = {
      "db": "nuccore",
      "id": contig_id,
      "rettype": "gb",
      "retmode": "xml"
  }

  for attempt in range(max_retries + 1):
    try:
      response = requests.get(url, params=params)
      if response.status_code == 200:
        xml_root = ElementTree.fromstring(response.content)
        for child in xml_root.iter('GBSeq_topology'):
          return child.text
      else:
        print(f"Error fetching data for {contig_id}: {response.status_code}")
    except (requests.exceptions.RequestException, MaxRetryError) as e:
      # Handle any request exceptions and MaxRetryError
      print(f"Attempt {attempt}/{max_retries}: Error fetching data for {contig_id}: {e}")
      if attempt < max_retries:
        time.sleep(backoff_factor * 2 ** attempt)  # Exponential backoff between retries
      else:
        return None

  # All retries failed
  print(f"Failed to fetch data for {contig_id} after {max_retries} retries.")
  return None

def read_contig_ids_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file]

def process_contigs(contig_list, batch_size=100, sleep_time=1):
  topology_results = {}
  for i in range(0, len(contig_list), batch_size):
    batch = contig_list[i:i+batch_size]
    for contig in batch:
      topology = get_contig_topology(contig)
      topology_results[contig] = topology
      print(f"Contig {contig} is {topology}")

      # Write results to file after each contig
      with open("topology_results.txt", "a") as output_file:
        output_file.write(f"{contig}\t{topology}\n")

      time.sleep(sleep_time)  # To avoid overwhelming the server
  return topology_results

contig_file = "contigs.txt" # The list of all your plasmid 
contig_list = read_contig_ids_from_file(contig_file)

# Process the contigs and get topology information
topology_results = process_contigs(contig_list)

# Write the results to a file
with open("topology_results.txt", "w") as output_file:
    for contig, topology in topology_results.items():
        output_file.write(f"{contig}\t{topology}\n")


```


## **Extract coverage information** 

Once the reads and assembly files have been downloaded, we ran **CoverM** (v0.6.1) (https://github.com/wwood/CoverM) to extract the coverage information, by using the following flags:

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

First, we extracted the Plasmid Taxonomic Units (PTUs) information of each cluster with **COPLA** (v1.0) (https://github.com/santirdnd/COPLA), using the following arguments: 

```diff
+ # python #
python3 bin/copla.py "$fasta_file" \
        databases/Copla_RS84/RS84f_sHSBM.pickle \
        databases/Copla_RS84/CoplaDB.fofn \
        "$fasta_file"_output

```

We also run **mob_suite** (v3.1.8) (https://github.com/phac-nml/mob-suite) on the assemblies, to extract replicon type information. We run it by paralellizing with the following command:

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
        
## **Extract plasmids with RNAI** 

In annotation files (.gff), we searched for those plasmids with replication through the RNAI-RNAII regulation system.  

```diff
+ # bash #

grep "RNAI;" *.gff > Files_with_RNAI.txt
sed 's/.gff3:contig_1//' Files_with_RNAI.txt > Files_with_RNAI_2.txt

```

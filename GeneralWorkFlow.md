**Extract data** 

First, we downloaded the metadata table from NCBI:


```diff
- text in red
+ text in green
! text in orange
# text in gray
@@ text in purple (and bold)@@
```
```diff
+ # bash #

# Both databases were used indistinctly, selecting for each genre, the one that contained most samples of our interest

wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt 
wget https://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt

```
Samples were selected by filtering the desired genus and "Complete Genome". For example:

```diff
@@ bash @@ 
grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt
```

Then, we used esearch to download the genome assemblies with the following arguments:

```diff
@@ bash @@ 
esearch -db assembly -query "biosample" | efetch -format fasta > biosample.fasta

```
And we analyze the number of contigs of each assembly file to filter out those that don't contain plasmids


```diff

@@ bash @@ 
mkdir LengthAssembly
for file in *.fasta *.fna; do
    awk '/^>/{if (l!="") print l; print; l=0; next}{l+=length($0)}END{print l}' "$file" > "LengthAssembly/$(basename -- "$file" .fna)"
done

@@ Python3 @@ 
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

Then, we downloaded the files containing run information for selected assemblies of NCBI also with esearch: 

```
@@ bash @@ 
esearch -db sra -query Biosample | efetch -format runinfo > Biosample.numbers
```

With the Biosample.numbers files, we use the run IDs to download the reads with fasterq-dump from samtools package:

```
@@ Python3 @@ 
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
Once the reads and assembly files have been downloaded, we ran **CoverM** to extract the coverage information:

```
#R #
path_to_reads="PATHTOREADS"
path_to_assemblies="PATHTOASSEMBLIES"
coverm <- finalruns %>% select(Run, AccessionNumber) %>% 
  mutate(run="coverm contig ") %>% 
  mutate(output=paste0("--output-file ", AccessionNumber)) %>% 
  mutate(method= "-m trimmed_mean ") %>% 
  mutate(reference= paste0("-r ",path_to_assemblies, AccessionNumber, ".fasta")) %>% 
  mutate(read1 = paste0("-1 ",path_to_reads, Run, "_1.fastq")) %>% 
  mutate(read2 = paste0("-2 ",path_to_reads, Run, "_2.fastq")) %>% 
  select(run, read1, read2, output, method, reference) %>% unique()
write.table(coverm, file="/XXXX/StaphCoverM.txt", sep="\t", quote = F, row.names = F, col.names = F)
```

We run this code in python, in parallel. Again, this step may take between hours and a couple days based on your computing capacity.
Tune the code to match your computing capacity.
```
#Python3 #
#Note wherever you run this code is where coverm results will appear. 
import multiprocessing
import subprocess

with open('StaphCoverM.txt', 'r') as file:
    commands = [line.strip() for line in file if line.strip()]

# Define the function that will execute each command
def execute_command(command):
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Command executed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}, Error: {e}")

if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=8) # Tune here how many cores you want to use
    pool.map(execute_command, commands)
    pool.close()
    pool.join()
```
We assume some of the mappings may fail, we intend not to lose more than 20% of the files at this step, but this may differ depending on the genre you are executing.
You will see empty files for the failed mappings, but be careful, because mappings in proccess also appear as empty files, and are only written when coverm is finished. 

Once finished. We parse the results with this custom code:
```
#bash #
#Note you have to be in the folder which contains the coverm results to run this code
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

We also run mobtyper (once again parallelising) on our .fasta files using the code:

```
#bash #
mkdir Resmobty
ls *.fasta *.fna | xargs -n 1 -P 8 -I {} sh -c 'mob_typer --multi --infile "{}" --out_file "Resmobty/{}"'
```
And parse the results using the code:
```
#bash #
for f in *.fasta; do awk -v fName="${f%.fasta}" '{printf("%s,%s\n", (FNR==1 ? "filename" : fName), $0)}' "$f" > mod"$f"; done
cat mod* > allmobtyperstaph.txt
```






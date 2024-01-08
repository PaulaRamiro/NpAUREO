First, download the metadata table from NCBI:

```
#bash #
  wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt # Both databases were used indistinctly, selecting for each genre, the one that contained most samples of our interest
  wget https://ftp.ncbi.nlm.nih.gov/genomes/refseq/assembly_summary_refseq.txt

```
Samples were selected by filtering the desired genus and  "Complete Genome".
For example:

```
#bash #
grep Staphylococcus assembly_summary_genbank.txt | grep "Complete Genome" > AllInfoStaph.txt
```
Now we create, with a custom R code, esearch orders to download .fasta assemblies from the table previously generated

```
#R #
Download.assemblies <- AllInfoStaph %>%
  mutate(ejecutar ="esearch -db assembly -query ") %>%
  mutate(genome = biosample ) %>%
  mutate(format = paste0("efetch -format fasta >", biosample, ".fasta")) %>%
  mutate(db= "| elink -target nucleotide -name \ assembly_nuccore_refseq |") %>% 
  select(ejecutar, genome, db, format)

```
We write this table and execute it as a shell command (sh FILENAME) #Note this step CANNOT be parallelized, due to NCBI server limit of petitions per second. If parallelized, will fail.

We then manually delete all empty or very small files (containing exclusively phage sequencing or just malformed files due to esearch fails), and those containing only 1 contig (no plasmids)

Then, two custom codes are run, to display all lengths of all contigs of each .fasta file, and filter out those that don't contain plasmids

```
#bash #
mkdir LengthAssembly
for file in *.fasta *.fna; do
    awk '/^>/{if (l!="") print l; print; l=0; next}{l+=length($0)}END{print l}' "$file" > "LengthAssembly/$(basename -- "$file" .fna)"
done
```
```
#Python3 #
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
This table, alllengths.txt, will be imported to R and used to filter.
A couple of column name changes are made due to incompatibilities in tables

Then, we create with the NCBI and our .fasta merged tables, esearch petitions to download .numbers files containing run information for selected assemblies


```
#R #
NCBI <- read.delim("/XXXX/AllInfoStaph.txt", sep = "\t")
FASTAS <- read.table("/XXXX/alllengths.txt", sep = ",",header = TRUE)
NCBI <- NCBI  %>% mutate(AccessionNumber=X.assembly_accession)#%>% mutate(BioSample=biosample)
FASTAS<-FASTAS %>% filter(grepl("complete", sample)) %>% select(BioSample)
FASTAS<-FASTAS %>% separate(Biosample, into = c("BioSample", "cosa"), sep="_ASM")
FASTAS<-FASTAS %>% mutate(Complete = "Yes") %>% unique()
FASTAS<-FASTAS %>% mutate(AccessionNumber = BioSample)
FASTASmNCBI<-FASTAS %>% left_join(NCBI) %>% filter(bioproject!="na") %>% mutate(BioSample=biosample)

Download.SRR <- FASTASmNCBI %>% select(biosample,AccessionNumber) %>% unique() %>% 
  mutate(ejecutar ="esearch -db sra -query ") %>%
  mutate(genome =  biosample) %>%
  mutate(format = paste0(" | efetch -format runinfo >", AccessionNumber, ".numbers")) %>%
  select(ejecutar, genome, format)
 write.table(Download.SRR, file="/XXXX/downloadnumbersstaph.sh",  row.names = FALSE,
            col.names = FALSE, quote = FALSE)
```
And execute this code in bash to download said files (sh downloadnumbersstaph.sh) (NOTE this code can neither be parallelized, due to same issue before with NCBI servers)

As done before, files with 0 bytes are discarded manually

All .numbers files are merged to be used as a table in R

```
#bash #
cat *.numbers > allnumbersstaph.txt
```
With the .numbers files, and all other information, we select pontentially valid Run numbers to download the .fastq files. 
Note we filter a lot because of disk space issues. Genres can have a size of over 1 or 2TB each.
```
#R #
SRR <- read.delim("/XXXX/allnumbersstaph.txt", sep = ",") %>% filter(Run != "Run") %>% filter(LibraryStrategy!="RNA-Seq") %>% filter(Platform=="ILLUMINA") %>% filter(LibraryLayout=="PAIRED")
finalruns <-  SRR %>% left_join(FASTASmNCBI) %>% unique()
finalruns %>% group_by(AccessionNumber) %>% summarise(N=n()) %>% filter(N!=1) %>% view()
finalruns<-finalruns %>% select(Run,AccessionNumber) %>% unique()
finalruns2<-finalruns %>% select(Run)
write.table(finalruns2, file = "/XXX/DefNumbers.txt",row.names = FALSE,col.names = FALSE, quote = FALSE)
```
This yields a list of SRRs with pontential to be used.
Now we execute a chunk of code that downloads all of the .fastq files available for selected runs using fasterq-dump from samtools package.
Using fastq-dump is also valid, but much slower. 
Note this code paralellizes in various procceses and can be tuned to match your machine capabilities. 

```
#Python3 #
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
This step may take between several hours and several days, based on your computing capacity and internet connection. 

Now, we prepare the code to run CoverM on all our samples.

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









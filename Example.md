This notebook serves as a guide to understanding how to run the code in the general workflow by using a particular example. 

First, we download NCBI metadata, and filter the genus, for example, "_Staphylococcus_" and those assemblies with complete genome. 

```diff

+ # bash #

# For Linux users:
wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt

#For MacOS users:
curl -O https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt

grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt

```
We select one random assembly from our dataset (GCA_001018645) to run the test. 

```diff
+ # bash #

grep "GCA_001018645" data_staphylococcus.txt > staphylococcus_example.txt
 
```
After identifying the Biosample ID in the assembly_summary_genbank.txt, we fetch the .fasta file:

```diff

+ # bash #

# For Linux users:
esearch -db assembly -query SAMN03255442 \
    | esummary \
    | xtract -pattern DocumentSummary -element FtpPath_GenBank \
    | while read -r line ;
    do
        fname=$(echo $line | grep -o 'GCA_.*' | sed 's/$/_genomic.fna.gz/') ;
        wget "$line/$fname" ;
    done

# For MacOS users:
esearch -db assembly -query SAMN03255442 \
    | esummary \
    | xtract -pattern DocumentSummary -element FtpPath_GenBank \
    | while read -r line ;
    do
        fname=$(echo $line | grep -o 'GCA_.*' | sed 's/$/_genomic.fna.gz/') ;
        curl -O "$line/$fname" ;
    done

 ```
Here, you can check the number of contigs and the length of each one with the script provided in the general workflow, although we will skip it here since there is only one file. 


 ```
+ # bash #

 awk '/^>/{if (l!="") print l; print; l=0; next}{l+=length($0)}END{print l}' _genomic.fna.gz

 ```
Now, we query the SRA database again with the biosample to get the .numbers file by filtering only those samples sequenced by Illumina and with paired ends. 

```diff

+ # bash #

esearch -db sra -query SAMN03255442 | efetch -format runinfo > SAMN03255442.numbers

grep "ILLUMINA" SAMN03255442.numbers | grep "PAIRED" > filtered_SAMN03255442.numbers

```
Now, by using the "Run" column, we can download the reads for each assembly with fasterq-dump:

```diff

+ # bash #

fasterq-dump --split-3 SRR1955495

```
Finally, we run CoverM on our downloaded assembly and reads to extract the coverage and to calculate the plasmid copy number. 

```diff

+ # bash #

coverm contig --output-file SAMN03255442 -m trimmed_mean -r SAMN03255442.fasta -1 SRR1955495_1.fastq -2 SRR1955495_2.fastq

```


This notebook serves as a guide to understand with a particular example how to run the workflow, we strongly encourage to try this approach with just one file before attempting to run more sequences at once. 


First, we download NCBI metadata, and filter one genus, for example, staphylococcus. 

```diff

+ # bash #
wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt 
grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt

```
In this case, we will only do it for one assembly, getting the first of the list does not guarantee the success so we will purposefully pick one in our final dataset to ensure its completeness (GCA_001018645). 

```diff

+ # bash #

grep "GCA_001018645" data_staphylococcus.txt > staphylococcus_example.txt
 
```
After identifying the Biosample field (headers from the first file assembly_summary_genbank.txt  may be used), we fetch the .fasta file.


```diff

+ # bash #

esearch -db assembly -query SAMN03255442 | elink -target nucleotide -name assembly_nuccore_refseq | efetch -format fasta > SAMN03255442.fasta
 ```
Here, you can check with the script provided in the general workflow the number of contigs and the length of each one, allthough we will skip it here since there is only one file. 

Now, we query the SRA database again with the biosample to get the .numbers file 
```diff

+ # bash #

esearch -db sra -query SAMN03255442 | efetch -format runinfo > SAMN03255442.numbers
```
We filter to get only Illumina and paired reads

```diff

+ # bash #

grep "ILLUMINA" SAMN03255442.numbers | grep "PAIRED" > filtered_SAMN03255442.numbers
```
Now, we download the corresponding reads using the Run column

```diff

+ # bash #

fasterq-dump --split-3 SRR1955495
```
Finally, we run coverm on our downloaded assembly and reads. 

```diff

+ # bash #
coverm contig --output-file SAMN03255442 -m trimmed_mean -r SAMN03255442.fasta -1 SRR1955495_1.fastq -2 SRR1955495_2.fastq
```

Which will output a file with the coverage of each contig. 

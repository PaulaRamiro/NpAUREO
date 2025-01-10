First, we download NCBI metadata, and filter one genus, for example, staphylococcus. 

```diff

+ # bash #
wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt 
grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt

```
In this case, we will only do it for one assembly, getting the first of the list does not guarantee the succes so we will purposefully pick one in our final dataset to ensure its completeness (GCA_001018645). 

```diff

+ # bash #

grep "GCA_001018645" data_staphylococcus.txt > staphylococcus_example.txt
 
```
After identifying the Biosample field ( (headers from the first file assembly_summary_genbank.txt  may be used), we fetch the .fasta file.


```diff

+ # bash #

esearch -db assembly -query SAMN03255442 | elink -target nucleotide -name assembly_nuccore_refseq | efetch -format fasta > SAMN03255442.fasta
 ```

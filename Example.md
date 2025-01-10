First, we download NCBI metadata, and filter one genus, for example, staphylococcus. 

```diff

+ # bash #
wget https://ftp.ncbi.nlm.nih.gov/genomes/genbank/assembly_summary_genbank.txt 
grep "Staphylococcus" assembly_summary_genbank.txt | grep "Complete Genome" > data_staphylococcus.txt

```
In this case, we will only do it for one assembly, getting the first of the list does not guarantee the succes so we will purposefully pick one in our final dataset to ensure its completeness (GCA_001018645). 

```diff

+ # bash #

grep *GCA_001018645* data_staphylococcus.txt > staphylococcus_example.txt
 
```

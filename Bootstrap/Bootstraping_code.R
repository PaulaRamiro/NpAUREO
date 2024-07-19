all_data <-read.table("Dataset1",header = T,fill = T,dec = ",",sep="\t") 

Indice1 = runif(10000, min=1, max=length(all_data$PCN))
Indice2 = runif(10000, min=1, max=length(all_data$PCN))
Indice3 = runif(10000, min=1, max=length(all_data$PCN))

PCN_boot = all_data$PCN[Indice1] 
Size_boot = all_data$Total_Size[Indice2] 
genomesize_boot = all_data$Length_chr[Indice3]

Bootstrapping <- data.frame(PCN_boot, Size_boot) %>% mutate(Total_DNA = PCN_boot*Size_boot) 
Bootstrapping_percen <- data.frame(PCN_boot, Size_boot) %>% mutate(percen = ((PCN_boot*Size_boot)/genomesize_boot)*100)

# Total plasmid percentage
Bootstrapping_percen  %>% 
   ggplot() +
   geom_density(aes(percen), color="#8366cbff", fill="#8366cbff", alpha=0.3) +
   geom_density(data=all_data, aes(percen), color="gray", fill="gray", alpha=0.2) +
   geom_jitter(aes(x=percen, y= -0.5, color=Size_boot>10000), width = 0, height = 0.05)+
   geom_jitter(data=all_data, aes(x=percen, y= -0.25, color=Total_Size>10000), width = 0, height = 0.05) +
   scale_x_log10(labels = scales::comma) +
   scale_y_continuous(labels = c("Bootstrapped","Observed", "0", "0.5", "1", "1.5"), breaks=c(-0.5, -0.25, 0, 0.5, 1, 1.5)) +
   theme_bw() +
   theme(panel.background = element_blank(), panel.grid = element_blank(),
          aspect.ratio = 1,
          legend.position = c(.95, .95),
    legend.justification = c("right", "top"),
    legend.box.just = "right",
    legend.margin = margin(6, 6, 6, 6),
          # legend.position = "none",
          strip.background = element_blank(),
          axis.title=element_text(size=13, face="bold"), 
          axis.text.x = element_text(size=11, vjust = 0.5),
          axis.text.y = element_text(size=11, vjust = 0.5))+
    scale_colour_manual(values =c("#8366cbff", "#95cea4ff")) +
    scale_fill_manual(values =c("#8366cbff", "#95cea4ff")) +
  labs(title = "Bootstrapping", x= "Percentage of plasmid DNA", y="Density")

# Total plasmid DNA
Bootstrapping  %>% 
   ggplot() +
   geom_density(aes(Total_DNA), color="#8366cbff", fill="#8366cbff", alpha=0.3) +
   geom_density(data=all_data, aes(Total_DNA_bases), color="gray", fill="gray", alpha=0.2) +
   geom_jitter(aes(x=Total_DNA, y= -0.5, color=Size_boot>10000), width = 0, height = 0.05)+
   geom_jitter(data=all_data, aes(x=Total_DNA_bases, y= -0.25, color=Total_Size>10000), width = 0, height = 0.05) +
   scale_x_log10(labels = scales::comma) +
   scale_y_continuous(labels = c("Bootstrapped","Observed", "0", "0.5", "1", "1.5"), breaks=c(-0.5, -0.25, 0, 0.5, 1, 1.5)) +
   theme_bw() +
   theme(panel.background = element_blank(), panel.grid = element_blank(),
          aspect.ratio = 1,
              legend.position = c(.95, .95),
    legend.justification = c("right", "top"),
    legend.box.just = "right",
    legend.margin = margin(6, 6, 6, 6),
          # legend.position = "none",
          strip.background = element_blank(),
          axis.title=element_text(size=13, face="bold"), 
          axis.text.x = element_text(size=11, vjust = 0.5),
          axis.text.y = element_text(size=11, vjust = 0.5))+
    scale_colour_manual(values =c("#8366cbff", "#95cea4ff")) +
    scale_fill_manual(values =c("#8366cbff", "#95cea4ff")) +
  labs(title = "Bootstrapping", x= "Percentage of plasmid DNA", y="Density")

real<-all_data %>% dplyr::select(Total_Size,PCN,percen)
real$Boostrap<- "No"
Bootstrapping_percen$Boostrap<- "Yes"
colnames(Bootstrapping_percen)[colnames(Bootstrapping_percen) == "PCN_boot"] <- "PCN"
colnames(Bootstrapping_percen)[colnames(Bootstrapping_percen) == "Size_boot"] <- "Total_Size"

bootstrap_real<-rbind(real,Bootstrapping_percen)
bootstrap_real<-bootstrap_real %>% mutate(percen=as.numeric(percen))

count_yes <- sum(bootstrap_real$Boostrap == "Yes")
count_no <- sum(bootstrap_real$Boostrap == "No")
print(c(Yes = count_yes, No = count_no))

ecdf_byes <- ecdf(bootstrap_real %>% filter(Boostrap == "Yes") %>% pull(percen))
ecdf_bno <- ecdf(bootstrap_real %>% filter(Boostrap == "No") %>% pull(percen))
grid_percen <- unique(bootstrap_real %>% pull(percen))
prob_acumulada_ecdf_byes <- ecdf_byes(v = grid_percen)
prob_acumulada_ecdf_bno <- ecdf_bno(v = grid_percen)
test_kolmogorov_smirnov <- ks.test(
        x = bootstrap_real  %>% filter(Boostrap == "Yes") %>% pull(percen),
        y = bootstrap_real  %>% filter(Boostrap == "No") %>% pull(percen)
      )
test_kolmogorov_smirnov

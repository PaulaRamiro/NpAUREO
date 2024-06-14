library(dplyr)
library("FactoMineR")
library("factoextra")

all_data <- read.delim("Supp.dataset.1.csv", sep="\t")

# Select numerical variables for PCA
numeric_vars <- c("gc", "Total_Size", "Length_chr", "Number_plasmids", "PCN")

# Subset data to numerical variables
data_numeric <- all_data %>% 
  select(numeric_vars)

# Scale numerical variables for PCA
data_numeric_scaled <- scale(data_numeric)

# Perform PCA
res_pca <- PCA(data_numeric_scaled, graph = FALSE)

# Print PCA results
print(res_pca)

# Variance explained by each principal component
fviz_eig(res_pca, addlabels = TRUE, ylim = c(0, 50))

# Biplot of variables and observations
fviz_pca_var(res_pca, col.var = "contrib",
             gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07"),
             repel = TRUE)

system.time({


library(readr)
library(dplyr)
library(ggplot2)
library(purrr)
library(stringr)


dataset_path <- "D:/PG/semester 3/R project/JATAYU_Dataset"
labels_dirs <- c(
  file.path(dataset_path, "train"),
  file.path(dataset_path, "valid"),
  file.path(dataset_path, "test")
)


class_names <- c("auto_rickshaw", "e_rickshaw", "cycle_rickshaw", 
                 "tractor_trolley", "motorcycle", "car", 
                 "bus", "truck", "bicycle", "pedestrian")


dir.create("docs/eda", recursive = TRUE, showWarnings = FALSE)
dir.create("r", showWarnings = FALSE)


cat("Scanning for label files...\n")
txt_files <- unlist(lapply(labels_dirs, function(d) {
  list.files(d, pattern = "\\.txt$", recursive = TRUE, full.names = TRUE)
}))
cat(sprintf("Found %d label files.\n", length(txt_files)))


read_yolo <- function(file) {
 
  lines <- readLines(file, warn = FALSE)
  if (length(lines) == 0) return(NULL)
  
  df <- read.table(text = lines, col.names = c("cls_id", "x", "y", "w", "h"), fill = TRUE)
  df$image_id <- basename(file)
  return(df)
}

cat("Parsing labels (this may take a minute)...\n")
all_labels <- bind_rows(lapply(txt_files, read_yolo))

if(nrow(all_labels) == 0) {
  stop("No labels found. Check the dataset path and format.")
}


all_labels <- all_labels %>%
  mutate(cls = class_names[cls_id + 1],
         box_area = w * h) 


class_counts <- all_labels %>% count(cls, sort = TRUE)
p1 <- ggplot(class_counts, aes(x = reorder(cls, n), y = n)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  coord_flip() +
  labs(title = "Total Objects per Class", x = "Class", y = "Count") +
  theme_minimal()
ggsave("docs/eda/class_frequency.png", p1, width = 8, height = 6)


img_counts <- all_labels %>% count(image_id)
p2 <- ggplot(img_counts, aes(x = n)) +
  geom_histogram(binwidth = 1, fill = "darkorange", color = "black") +
  labs(title = "Distribution of Objects per Image", x = "Objects per Image", y = "Frequency") +
  theme_minimal()
ggsave("docs/eda/objects_per_image.png", p2, width = 8, height = 6)


p3 <- ggplot(all_labels, aes(x = cls, y = box_area)) +
  geom_boxplot(fill = "lightblue") +
  coord_flip() +
  labs(title = "Relative Box Area per Class (120m altitude)", x = "Class", y = "Relative Area (w * h)") +
  theme_minimal()
ggsave("docs/eda/box_size_dist.png", p3, width = 8, height = 6)

cat("EDA plots saved to docs/eda/.\n")


total_objects <- sum(class_counts$n)
dirichlet_prior <- class_counts %>%
  mutate(
    alpha = n + 1,
    share = n / total_objects
  ) %>%
  select(cls, alpha, share)

write_csv(dirichlet_prior, "class_prior.csv")
cat("Saved r/class_prior.csv\n")


img_class_counts <- all_labels %>%
  count(image_id, cls) %>%
  tidyr::pivot_wider(names_from = cls, values_from = n, values_fill = list(n = 0))


count_stats <- img_class_counts %>%
  tidyr::pivot_longer(cols = -image_id, names_to = "cls", values_to = "count") %>%
  group_by(cls) %>%
  summarize(
    mean_count = mean(count),
    var_count = var(count),
    dispersion_index = var_count / mean_count,
    .groups = "drop"
  )

write_csv(count_stats, "count_stats.csv")
cat("Saved r/count_stats.csv\n")


report_file <- "docs/EDA_FINDINGS.md"
cat("# JATAYUv1.0 EDA & Priors Findings\n\n", file = report_file)
cat("## Class Imbalance\n", file = report_file, append = TRUE)
cat(sprintf("Total objects analyzed: %d\n", total_objects), file = report_file, append = TRUE)
cat("Most frequent classes: ", paste(head(class_counts$cls, 3), collapse=", "), "\n", file = report_file, append = TRUE)
cat("Least frequent classes: ", paste(tail(class_counts$cls, 3), collapse=", "), "\n\n", file = report_file, append = TRUE)

cat("## Count Distribution Analysis (Poisson vs Negative Binomial)\n", file = report_file, append = TRUE)
cat("A standard Poisson distribution assumes the mean equals the variance (Dispersion Index ≈ 1.0).\n", file = report_file, append = TRUE)
cat("If Dispersion Index > 1, the data is overdispersed and requires a Negative Binomial model for anomaly detection.\n\n", file = report_file, append = TRUE)

disp_summary <- count_stats %>% 
  mutate(status = ifelse(dispersion_index > 1.5, "Overdispersed (Use NegBin)", "Poisson-like"))

for(i in 1:nrow(disp_summary)) {
  cat(sprintf("* **%s**: Mean = %.2f, Var = %.2f, Dispersion = %.2f -> %s\n",
              disp_summary$cls[i], disp_summary$mean_count[i], 
              disp_summary$var_count[i], disp_summary$dispersion_index[i],
              disp_summary$status[i]), file = report_file, append = TRUE)
}

cat("\nEDA script completed successfully.\n")

  ans <- sum(1:1e7)
})
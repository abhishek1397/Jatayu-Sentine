
library(dplyr)

class_priors <- read.csv("r/class_prior.csv", stringsAsFactors = FALSE)
count_stats <- read.csv("r/count_stats.csv", stringsAsFactors = FALSE)

get_anomaly_prob <- function(cls_name, observed_count) {
  stats <- count_stats %>% filter(cls == cls_name)
  if (nrow(stats) == 0) return(1.0)
  
  mu <- stats$mean_count
  var_c <- stats$var_count
  if (var_c <= mu) {
    var_c <- mu + 0.5
  }
  
  beta_prior <- mu / (var_c - mu)
  alpha_prior <- mu * beta_prior
  
  size_nb <- alpha_prior
  prob_nb <- beta_prior / (beta_prior + 1)
  
  tail_prob <- pnbinom(observed_count - 1, size = size_nb, prob = prob_nb, lower.tail = FALSE)
  return(tail_prob)
}

get_dirichlet_posterior <- function(current_counts_df) {
  merged <- class_priors %>%
    left_join(current_counts_df, by = "cls") %>%
    mutate(
      observed = ifelse(is.na(vehicles), 0, as.numeric(vehicles)),
      
      alpha_effective = 1.0,
      alpha_post = alpha_effective + observed,
      post_share = alpha_post / sum(alpha_post)
    )
  return(merged)
}
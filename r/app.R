# r/app.R
library(shiny)
library(DBI)
library(RPostgres)
library(dplyr)
library(ggplot2)
library(DT)

source("stats_functions.R")

# Database connection function
get_db_conn <- function() {
  dbConnect(RPostgres::Postgres(),
            dbname = "jatayu_db",
            host = "127.0.0.1",
            port = 5432,
            user = "jatayu_user",
            password = "jatayu_password")
}

# UI Definition (Universal Shiny Dark Theme)
ui <- fluidPage(
  tags$head(
    tags$style(HTML("
      body { background-color: #0b0f19; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
      .well { background-color: #161e2e; border: 1px solid #2d3748; border-radius: 8px; box-shadow: none; }
      .kpi-card { background: #1a2234; border: 1px solid #2d3748; border-radius: 8px; padding: 16px; margin-bottom: 15px; }
      .kpi-title { font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
      .kpi-value { font-size: 28px; font-weight: 700; margin-top: 4px; }
      .card-box { background: #161e2e; border: 1px solid #2d3748; border-radius: 8px; padding: 18px; margin-bottom: 20px; }
      .card-header-custom { font-size: 15px; font-weight: 600; color: #38bdf8; margin-bottom: 12px; border-bottom: 1px solid #2d3748; padding-bottom: 6px; }
      .form-control { background-color: #0f172a; border: 1px solid #334155; color: #f8fafc; }
      .form-control:focus { background-color: #0f172a; border-color: #38bdf8; color: #f8fafc; }
      .table-dark { background-color: #161e2e; color: #e2e8f0; }
    "))
  ),
  
  titlePanel(
    div(style = "margin-top: 10px; margin-bottom: 15px;",
        span("JATAYU-SENTINEL", style = "font-weight: 800; color: #38bdf8;"),
        span(" | Real-Time Aerial Traffic Surveillance", style = "font-weight: 300; font-size: 18px; color: #94a3b8;")
    )
  ),
  
  sidebarLayout(
    sidebarPanel(
      width = 3,
      h4("Controls", style = "color: #f8fafc; font-weight: 600;"),
      numericInput("anomaly_thresh", "Anomaly Threshold (p-value):", value = 0.05, min = 0.001, max = 0.2, step = 0.01),
      numericInput("history_mins", "History Window (Minutes):", value = 5, min = 1, max = 60),
      actionButton("refresh", "Force Refresh", class = "btn-primary", style = "width: 100%; margin-top: 5px;"),
      hr(style = "border-color: #334155;"),
      h5("Telemetry Status", style = "color: #94a3b8; font-weight: 600;"),
      textOutput("last_update")
    ),
    
    mainPanel(
      width = 9,
      
      # KPI Row
      fluidRow(
        column(4, div(class = "kpi-card",
                      div(class = "kpi-title", "Total Vehicles (Last Min)"),
                      div(class = "kpi-value", style = "color: #10b981;", textOutput("kpi_total")))),
        column(4, div(class = "kpi-card",
                      div(class = "kpi-title", "Active Anomalies"),
                      div(class = "kpi-value", style = "color: #ef4444;", textOutput("kpi_anomalies")))),
        column(4, div(class = "kpi-card",
                      div(class = "kpi-title", "Dominant Class"),
                      div(class = "kpi-value", style = "color: #38bdf8;", textOutput("kpi_dominant"))))
      ),
      
      # --- LIVE VIDEO FEED SECTION ---
      div(class = "card-box",
          div(class = "card-header-custom", "Live Drone Feed"),
          HTML('<img src="http://127.0.0.1:5000/video_feed" style="width:100%; max-height:450px; object-fit:contain; border-radius:4px; background-color:#0b0f19;">')
      ),
      # -------------------------------

      # Live Time Series
      div(class = "card-box",
          div(class = "card-header-custom", "Live Vehicle Counts per Class (10s Tumbling Windows)"),
          plotOutput("ts_plot", height = "280px")
      ),
      
      # Bayesian Panels Row
      fluidRow(
        column(6, div(class = "card-box",
                      div(class = "card-header-custom", "Bayesian Anomaly Alerts (Gamma-Poisson)"),
                      DTOutput("alert_table"))),
        column(6, div(class = "card-box",
                      div(class = "card-header-custom", "Class-Mix Shift (Dirichlet Posterior vs Prior)"),
                      plotOutput("dirichlet_plot", height = "280px")))
      )
    )
  )
)

# Server Logic
server <- function(input, output, session) {
  
  # Auto-refresh polling every 5 seconds
  auto_invalidate <- reactiveTimer(5000)
  
  live_data <- reactive({
    auto_invalidate()
    input$refresh
    
    conn <- tryCatch(get_db_conn(), error = function(e) NULL)
    if (is.null(conn)) return(data.frame())
    on.exit(dbDisconnect(conn))
    
    cutoff <- Sys.time() - (input$history_mins * 60)
    
    query <- "SELECT window_start, cls, vehicles 
              FROM window_counts_filled 
              WHERE window_start >= $1 
              ORDER BY window_start ASC"
    
    df <- tryCatch(
      dbGetQuery(conn, query, params = list(cutoff)),
      error = function(e) data.frame()
    )
    
    if (nrow(df) > 0) {
      df$window_start <- as.POSIXct(df$window_start, tz = "UTC")
      attr(df$window_start, "tzone") <- Sys.timezone()
    }
    return(df)
  })
  
  latest_window <- reactive({
    df <- live_data()
    if (nrow(df) == 0) return(data.frame())
    max_time <- max(df$window_start)
    df %>% filter(window_start == max_time)
  })
  
  # KPI Outputs
  output$last_update <- renderText({
    paste("Last DB fetch:", format(Sys.time(), "%H:%M:%S"))
  })
  
  output$kpi_total <- renderText({
    df <- live_data()
    if (nrow(df) == 0) return("0")
    last_min_cutoff <- max(df$window_start) - 60
    as.character(sum(df$vehicles[df$window_start >= last_min_cutoff]))
  })
  
  output$kpi_dominant <- renderText({
    latest <- latest_window()
    if (nrow(latest) == 0 || sum(latest$vehicles) == 0) return("None")
    latest$cls[which.max(latest$vehicles)]
  })
  
  # Time Series Plot
  output$ts_plot <- renderPlot({
    df <- live_data()
    if (nrow(df) == 0) {
      return(ggplot() + theme_void() + 
               annotate("text", x = 1, y = 1, label = "Awaiting Spark streaming data in Postgres...", color = "gray60", size = 5))
    }
    
    ggplot(df, aes(x = window_start, y = vehicles, color = cls)) +
      geom_line(size = 1) +
      geom_point(size = 1.5) +
      theme_minimal() +
      labs(x = "Time", y = "Vehicles", color = "Class") +
      theme(
        plot.background = element_rect(fill = "#161e2e", color = NA),
        panel.background = element_rect(fill = "#161e2e", color = NA),
        text = element_text(color = "white"),
        axis.text = element_text(color = "gray70"),
        panel.grid.major = element_line(color = "#2d3748"),
        panel.grid.minor = element_blank(),
        legend.position = "bottom",
        legend.background = element_rect(fill = "#161e2e", color = NA)
      )
  }, bg = "transparent")
  
  # Anomaly Table
  anomalies_df <- reactive({
    latest <- latest_window()
    if (nrow(latest) == 0) return(data.frame())
    
    latest$p_value <- sapply(1:nrow(latest), function(i) {
      get_anomaly_prob(latest$cls[i], latest$vehicles[i])
    })
    
    latest %>%
      mutate(status = ifelse(p_value < input$anomaly_thresh, "🚨 ANOMALY", "Normal")) %>%
      filter(status == "🚨 ANOMALY" | vehicles > 0) %>%
      select(cls, vehicles, p_value, status) %>%
      arrange(p_value)
  })
  
  output$alert_table <- renderDT({
    df <- anomalies_df()
    if (nrow(df) == 0) {
      return(datatable(data.frame(Message = "No detections in active window"), 
                       options = list(dom = 't'), rownames = FALSE))
    }
    datatable(df, options = list(dom = 't', pageLength = 10), rownames = FALSE) %>%
      formatRound("p_value", 4) %>%
      formatStyle('status', color = styleEqual(c("🚨 ANOMALY", "Normal"), c('#ef4444', '#10b981')))
  })
  
  output$kpi_anomalies <- renderText({
    df <- anomalies_df()
    if (nrow(df) == 0) return("0")
    as.character(sum(df$status == "🚨 ANOMALY"))
  })
  
  # Dirichlet Plot
  output$dirichlet_plot <- renderPlot({
    latest <- latest_window()
    if (nrow(latest) == 0) {
      return(ggplot() + theme_void() + 
               annotate("text", x = 1, y = 1, label = "Awaiting window data...", color = "gray60", size = 5))
    }
    
    post <- get_dirichlet_posterior(latest)
    
    ggplot(post, aes(x = reorder(cls, post_share), y = post_share)) +
      geom_col(fill = "#0284c7", alpha = 0.85) +
      geom_point(aes(y = share), color = "#f43f5e", size = 3) +
      coord_flip() +
      theme_minimal() +
      labs(x = "Class", y = "Posterior Share (Bars) vs Prior (Red Dots)") +
      theme(
        plot.background = element_rect(fill = "#161e2e", color = NA),
        panel.background = element_rect(fill = "#161e2e", color = NA),
        text = element_text(color = "white"),
        axis.text = element_text(color = "gray70"),
        panel.grid.major.x = element_line(color = "#2d3748"),
        panel.grid.minor = element_blank()
      )
  }, bg = "transparent")
}

shinyApp(ui, server)
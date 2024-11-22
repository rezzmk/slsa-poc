
using System.Diagnostics.Metrics;
using Prometheus;

namespace ssle_service;

public static class PrometheusMetricsConfig
{
    public static void ConfigureMetrics(this WebApplicationBuilder builder)
    {
        builder.Services.AddSingleton<CollectorRegistry>();
        builder.Services.AddMetrics(); // Optional if you're adding metrics via middleware
    }

    public static void UseMetricsMiddleware(this WebApplication app)
    {
        // Expose /metrics endpoint for Prometheus
        app.UseHttpMetrics();

        // Custom metrics
        var requestCounter = Metrics.CreateCounter("http_requests_received_total", 
            "Number of HTTP requests received", 
            new CounterConfiguration
            {
                LabelNames = new[] { "method", "endpoint" }
            });

        var requestDuration = Metrics.CreateHistogram("http_request_duration_seconds", 
            "HTTP request duration in seconds", 
            new HistogramConfiguration
            {
                LabelNames = new[] { "method", "endpoint" },
                Buckets = Histogram.ExponentialBuckets(0.001, 2, 10) // Example buckets
            });

        var inProgressRequests = Metrics.CreateGauge("http_requests_in_progress", 
            "Number of requests currently in progress", 
            new GaugeConfiguration
            {
                LabelNames = new[] { "method", "endpoint" }
            });

        app.Use((RequestDelegate next) => async context =>
        {
            var method = context.Request.Method;
            var endpoint = context.Request.Path.Value ?? "unknown";

            inProgressRequests.WithLabels(method, endpoint).Inc();
            var timer = requestDuration.WithLabels(method, endpoint).NewTimer();

            try
            {
                requestCounter.WithLabels(method, endpoint).Inc();
                await next(context); // Explicitly pass the context to the next middleware
            }
            finally
            {
                timer.Dispose();
                inProgressRequests.WithLabels(method, endpoint).Dec();
            }
        });
    }    
}
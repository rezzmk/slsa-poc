using Prometheus;
using Microsoft.AspNetCore.Builder;

public static class PrometheusMetricsConfig
{
    private static readonly Counter ResponseBytes = Metrics
        .CreateCounter("http_response_bytes_total", "Total size of HTTP responses in bytes",
            new CounterConfiguration
            {
                LabelNames = new[] { "method", "endpoint", "client_ip" }
            });

    private static readonly Counter RequestsTotal = Metrics
        .CreateCounter("http_requests_total", "Total number of HTTP requests",
            new CounterConfiguration
            {
                LabelNames = new[] { "method", "endpoint", "status", "client_ip" }
            });

    private static readonly Gauge RequestsInProgress = Metrics
        .CreateGauge("http_requests_in_progress", "Number of requests currently being processed",
            new GaugeConfiguration
            {
                LabelNames = new[] { "method", "client_ip" }
            });

    public static void ConfigureMetrics(WebApplication app)
    {
        app.UseMetricServer();

        // Configure HTTP metrics middleware with custom labels
        app.UseHttpMetrics(options =>
        {
            options.AddCustomLabel("client_ip", context => 
                context.Connection.RemoteIpAddress?.ToString() ?? "unknown");
        });
    }

    public static IDisposable TrackRequest(string method, string clientIp)
    {
        RequestsInProgress.Labels(method, clientIp).Inc();
        return new RequestTracker(method, clientIp);
    }

    public static void RecordRequest(string method, string endpoint, string status, string clientIp, long responseSize)
    {
        RequestsTotal.Labels(method, endpoint, status, clientIp).Inc();
        ResponseBytes.Labels(method, endpoint, clientIp).Inc(responseSize);
    }

    private class RequestTracker : IDisposable
    {
        private readonly string _method;
        private readonly string _clientIp;

        public RequestTracker(string method, string clientIp)
        {
            _method = method;
            _clientIp = clientIp;
        }

        public void Dispose()
        {
            RequestsInProgress.Labels(_method, _clientIp).Dec();
        }
    }
}

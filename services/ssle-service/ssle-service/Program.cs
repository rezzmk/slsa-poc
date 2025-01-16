using Prometheus;
using Serilog;
using ssle_service;

var builder = WebApplication.CreateBuilder(args);

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .WriteTo.Console()
    .WriteTo.File("/app/logs/app.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddHttpClient("ServiceDiscovery");

var serviceDiscoveryOptions = new ServiceDiscoveryOptions
{
    ServiceName = builder.Configuration["SERVICE_NAME"] ?? "unknown-service",
    ServiceType = "web-api",
    RegistryUrl = builder.Configuration["RegistryUrl"] ?? "http://registry-service:8080/registry",
    HeartbeatInterval = TimeSpan.FromSeconds(30),
    Metadata = new Dictionary<string, string>
    {
        { "version", "1.0" },
        { "environment", builder.Environment.EnvironmentName }
    }
};

var serverUrl = builder.Configuration["ASPNETCORE_URLS"]?.Split(';').FirstOrDefault() ?? "http://localhost:8080";
builder.Services.AddHostedService(sp => new ServiceDiscoveryService(
    sp.GetRequiredService<IHttpClientFactory>(),
    serviceDiscoveryOptions,
    serverUrl));


var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Configure metrics middleware
app.Use(async (context, next) =>
{
    var clientIp = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
    var method = context.Request.Method;
    var endpoint = context.Request.Path.Value ?? "/";

    using (PrometheusMetricsConfig.TrackRequest(method, clientIp))
    {
        var originalBodyStream = context.Response.Body;
        using var memStream = new MemoryStream();
        context.Response.Body = memStream;

        await next();

        var responseLength = memStream.Length;
        memStream.Position = 0;
        await memStream.CopyToAsync(originalBodyStream);

        PrometheusMetricsConfig.RecordRequest(
            method, 
            endpoint, 
            context.Response.StatusCode.ToString(),
            clientIp,
            responseLength
        );
    }
});

// Configure metrics
PrometheusMetricsConfig.ConfigureMetrics(app);

app.MapControllers();

app.Run();

using Prometheus;
using Serilog;

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

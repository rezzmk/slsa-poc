using Microsoft.AspNetCore.HttpLogging;
using Prometheus;
using Serilog;

namespace ssle_service;

public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add Serilog
        Log.Logger = new LoggerConfiguration()
            .WriteTo.Console()
            .WriteTo.File("/app/logs/app.log", rollingInterval: RollingInterval.Day)
            .CreateLogger();

        builder.Host.UseSerilog();

        // Add HTTP logging
        builder.Services.AddHttpLogging(logging =>
        {
            logging.LoggingFields = HttpLoggingFields.All;
            logging.RequestHeaders.Add("x-request-id");
            logging.ResponseHeaders.Add("x-response-id");
        });

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

        app.UseHttpsRedirection();
        app.UseAuthorization();
        app.MapControllers();

        // Prometheus metrics endpoint
        app.MapMetrics();

        app.MapGet("/", (HttpContext context) =>
        {
            Log.Information(
                "Request received from {IpAddress} with User-Agent {UserAgent}",
                context.Connection.RemoteIpAddress,
                context.Request.Headers.UserAgent.ToString()
            );

            RequestCounter.Inc();
            return "Hello World!";
        });

        app.Run();
    }
    
    private static readonly Counter RequestCounter = Metrics.CreateCounter(
        "http_requests_total", 
        "Total number of HTTP requests");
}

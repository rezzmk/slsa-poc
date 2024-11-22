using Microsoft.AspNetCore.HttpLogging;
using Prometheus;
using Serilog;
using Serilog.Formatting.Compact;
using Serilog.Formatting.Json;

namespace ssle_service;

public class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add Serilog
        Log.Logger = new LoggerConfiguration()
            .WriteTo.Console()
            .WriteTo.File(
                new CompactJsonFormatter(),
                "/app/logs/app.log", rollingInterval: RollingInterval.Day)
            .CreateLogger();

        /*
        builder.Host.UseSerilog((context, config) => {
            config.WriteTo.File(
                new CompactJsonFormatter(),
                "/app/logs/webservice.log",
                rollingInterval: RollingInterval.Day
                //outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{Level}] {Message} {Exception}{NewLine}"
            );
        });
        */

        // Add HTTP logging
        /*
        builder.Services.AddHttpLogging(logging =>
        {
            logging.LoggingFields = HttpLoggingFields.All;
            logging.RequestHeaders.Add("x-request-id");
            logging.ResponseHeaders.Add("x-response-id");
        });
        */

        // Add services to the container.
        builder.Services.AddControllers();
        builder.Services.AddEndpointsApiExplorer();
        builder.Services.AddSwaggerGen();

        var app = builder.Build();

        app.UseHttpMetrics(options =>
        {
            options.AddCustomLabel(
                "client_ip_address", 
                context => context.Connection.RemoteIpAddress?.MapToIPv4()?.ToString() ?? "unknown");
        });

        // Configure the HTTP request pipeline.
        if (app.Environment.IsDevelopment())
        {
            app.UseSwagger();
            app.UseSwaggerUI();
        }

        app.UseHttpsRedirection();
        app.UseAuthorization();
        app.MapControllers();

        app.MapMetrics();

        app.Run();
    }
}

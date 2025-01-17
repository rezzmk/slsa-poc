using System.Text;
using System.Text.Json;

namespace ssle_service;

public class ServiceRegistry {
    public string ServiceName { get; set; }
    public string ServiceUrl { get; set; }
    public string ServiceType { get; set; }
    public Dictionary<string, string> Metadata { get; set; }
    public DateTime LastHeartbeat { get; set; }
}

public class ServiceDiscoveryOptions {
    public string ServiceName { get; set; }
    public string ServiceType { get; set; }
    public string RegistryUrl { get; set; }
    public TimeSpan HeartbeatInterval { get; set; } = TimeSpan.FromSeconds(30);
    public Dictionary<string, string> Metadata { get; set; }
}

public class ServiceDiscoveryService : IHostedService, IDisposable {
    private readonly HttpClient _httpClient;
    private readonly ServiceDiscoveryOptions _options;
    private readonly string _serviceUrl;
    private Timer _heartbeatTimer;
    private bool _isRegistered;

    public ServiceDiscoveryService(
        IHttpClientFactory httpClientFactory,
        ServiceDiscoveryOptions options,
        string serviceUrl) {
        _httpClient = httpClientFactory.CreateClient("ServiceDiscovery");
        _options = options;
        _serviceUrl = serviceUrl;
    }

    public async Task StartAsync(CancellationToken cancellationToken) {
        await RegisterServiceAsync();
        _heartbeatTimer = new Timer(SendHeartbeat, null, TimeSpan.Zero, _options.HeartbeatInterval);
    }

    public async Task StopAsync(CancellationToken cancellationToken) {
        if (_heartbeatTimer != null) {
            await _heartbeatTimer.DisposeAsync();
        }

        await DeregisterServiceAsync();
    }

    private async Task RegisterServiceAsync()
    {
        var registration = new ServiceRegistry {
            ServiceName = _options.ServiceName,
            ServiceUrl = _serviceUrl,
            ServiceType = _options.ServiceType,
            Metadata = _options.Metadata ?? new Dictionary<string, string>(),
            LastHeartbeat = DateTime.UtcNow
        };

        var content = new StringContent(
            JsonSerializer.Serialize(registration),
            Encoding.UTF8,
            "application/json");

        try {
            var response = await _httpClient.PostAsync($"{_options.RegistryUrl}/register", content);
            response.EnsureSuccessStatusCode();
            _isRegistered = true;
        }
        catch (Exception ex) {
            Console.WriteLine($"Failed to register service: {ex.Message}");
        }
    }

    private async Task DeregisterServiceAsync() {
        if (!_isRegistered) return;

        try {
            var response = await _httpClient.DeleteAsync(
                $"{_options.RegistryUrl}/deregister/{_options.ServiceName}");
            response.EnsureSuccessStatusCode();
        }
        catch (Exception ex) {
            Console.WriteLine($"Failed to deregister service: {ex.Message}");
        }
    }

    private async void SendHeartbeat(object state) {
        if (!_isRegistered) {
            await RegisterServiceAsync();
            return;
        }

        try {
            var heartbeat = new {
                ServiceName = _options.ServiceName,
                Timestamp = DateTime.UtcNow
            };

            var content = new StringContent(
                JsonSerializer.Serialize(heartbeat),
                Encoding.UTF8,
                "application/json");

            var response = await _httpClient.PostAsync(
                $"{_options.RegistryUrl}/heartbeat",
                content);

            response.EnsureSuccessStatusCode();
        }
        catch (Exception ex) {
            Console.WriteLine($"Failed to send heartbeat: {ex.Message}");
            _isRegistered = false; 
        }
    }

    public void Dispose() {
        _heartbeatTimer?.Dispose();
    }
}

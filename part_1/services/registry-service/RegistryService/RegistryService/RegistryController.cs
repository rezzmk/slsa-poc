
using Microsoft.AspNetCore.Mvc;
using System.Collections.Concurrent;

namespace RegistryService;

[ApiController]
[Route("[controller]")]
public class RegistryController : ControllerBase
{
    private static readonly ConcurrentDictionary<string, ServiceRegistry> _services = new();
    private readonly ILogger<RegistryController> _logger;
    private readonly Timer _cleanupTimer;

    public RegistryController(ILogger<RegistryController> logger)
    {
        _logger = logger;
        _cleanupTimer = new Timer(CleanupStaleServices, null, TimeSpan.Zero, TimeSpan.FromMinutes(1));
    }

    [HttpPost("register")]
    public IActionResult Register(ServiceRegistry registration)
    {
        if (string.IsNullOrWhiteSpace(registration.ServiceName) || 
            string.IsNullOrWhiteSpace(registration.ServiceUrl))
        {
            return BadRequest("Service name and URL are required");
        }

        registration.LastHeartbeat = DateTime.UtcNow;
        _services.AddOrUpdate(registration.ServiceName, registration, (_, _) => registration);
        _logger.LogInformation($"Service registered: {registration.ServiceName} at {registration.ServiceUrl}");
        
        return Ok(registration);
    }

    [HttpDelete("deregister/{serviceName}")]
    public IActionResult Deregister(string serviceName)
    {
        if (_services.TryRemove(serviceName, out var service))
        {
            _logger.LogInformation($"Service deregistered: {serviceName}");
            return Ok(service);
        }

        return NotFound();
    }

    [HttpPost("heartbeat")]
    public IActionResult Heartbeat(HeartbeatRequest request)
    {
        if (_services.TryGetValue(request.ServiceName, out var service))
        {
            service.LastHeartbeat = DateTime.UtcNow;
            return Ok();
        }

        return NotFound();
    }

    [HttpGet("services")]
    public IActionResult GetServices([FromQuery] string serviceType = null)
    {
        var services = _services.Values;
        
        if (!string.IsNullOrWhiteSpace(serviceType))
        {
            services = (ICollection<ServiceRegistry>)services.Where(s => s.ServiceType.Equals(serviceType, StringComparison.OrdinalIgnoreCase));
        }

        return Ok(services);
    }

    [HttpGet("services/{serviceName}")]
    public IActionResult GetService(string serviceName)
    {
        if (_services.TryGetValue(serviceName, out var service))
        {
            return Ok(service);
        }

        return NotFound();
    }

    private void CleanupStaleServices(object state)
    {
        var staleThreshold = DateTime.UtcNow.AddMinutes(-2);
        var staleServices = _services.Values
            .Where(s => s.LastHeartbeat < staleThreshold)
            .Select(s => s.ServiceName)
            .ToList();

        foreach (var serviceName in staleServices)
        {
            if (_services.TryRemove(serviceName, out var service))
            {
                _logger.LogWarning($"Removed stale service: {serviceName}, Last heartbeat: {service.LastHeartbeat}");
            }
        }
    }

    public class HeartbeatRequest
    {
        public string ServiceName { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
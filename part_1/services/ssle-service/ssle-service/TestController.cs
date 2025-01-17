using Microsoft.AspNetCore.Mvc;
using System.Text;

namespace ssle_service.Controllers;

[ApiController]
[Route("api")]
public class TestController : ControllerBase
{
    private static readonly Random random = new Random();

    // Change this method in the TestController
	public IActionResult Forbidden()
	{
	    return StatusCode(403);
	}

    // Endpoint for testing auth failures
    [HttpGet("admin")]
    public IActionResult Admin()
    {
        // Randomly return 401/403 to simulate auth failures
        if (random.NextDouble() < 0.8)
        {
            return Unauthorized();
        }
        return Ok(new { message = "Admin area" });
    }

    // Endpoint for testing data exfiltration
    [HttpGet("data")]
    public IActionResult GetData([FromQuery] int size = 1024)
    {
        // Generate dummy data of requested size (limited to prevent abuse)
        var maxSize = Math.Min(size, 5 * 1024 * 1024); // 5MB max
        var data = new string('A', maxSize);
        return Ok(new { data });
    }

    // Endpoint for testing persistence/C2
    [HttpPost("beacon")]
    public IActionResult Beacon([FromBody] object data)
    {
        // Simulate processing time
        Thread.Sleep(random.Next(100, 500));
        return Ok(new { status = "received" });
    }

    // Regular endpoint that always works (baseline)
    [HttpGet("status")]
    public IActionResult Status()
    {
        return Ok(new { status = "operational" });
    }

    // Endpoint that looks like it might contain sensitive info
    [HttpGet("users")]
    public IActionResult Users()
    {
        if (random.NextDouble() < 0.9)
        {
            return Unauthorized();
        }
        return Ok(new { message = "User list" });
    }

    // Configuration endpoint - common target
    [HttpGet("config")]
    public IActionResult Config()
    {
        if (random.NextDouble() < 0.9)
        {
            return Forbidden();
        }
        return Ok(new { message = "System configuration" });
    }
}

using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc;

namespace API.Controllers;

[Route("api/[controller]")]
[ApiController]
public class FaceCameraController : ControllerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly string _serviceBaseUrl;

    public FaceCameraController(IHttpClientFactory httpClientFactory, IConfiguration configuration)
    {
        _httpClientFactory = httpClientFactory;
        _serviceBaseUrl = ResolveServiceBaseUrl(
            configuration["AiServices:FaceCameraBaseUrl"],
            "http://127.0.0.1:5001/api"
        );
    }

    [HttpPost("camera/on")]
    public Task<IActionResult> TurnOnCamera([FromBody] CameraOnRequest request) =>
        ProxyPostJsonAsync("/camera/on", request);

    [HttpPost("camera/off")]
    public Task<IActionResult> TurnOffCamera() =>
        ProxyPostAsync("/camera/off");

    [HttpPost("camera/reset")]
    public Task<IActionResult> ResetCameraState() =>
        ProxyPostAsync("/camera/reset");

    [HttpGet("camera/status")]
    public Task<IActionResult> GetCameraStatus() =>
        ProxyGetAsync("/camera/status");

    [HttpGet("camera/result")]
    public Task<IActionResult> GetCameraResult() =>
        ProxyGetAsync("/camera/result");

    [HttpGet("camera/locked-images")]
    public Task<IActionResult> GetLockedImages() =>
        ProxyGetAsync("/camera/locked-images");

    private async Task<IActionResult> ProxyGetAsync(string relativePath)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            var response = await client.GetAsync(BuildServiceUrl(relativePath));
            var content = await response.Content.ReadAsStringAsync();

            return new ContentResult
            {
                StatusCode = (int)response.StatusCode,
                Content = content,
                ContentType = "application/json"
            };
        }
        catch (Exception ex)
        {
            return StatusCode(503, new { message = $"Khong the ket noi toi Face camera service: {ex.Message}" });
        }
    }

    private async Task<IActionResult> ProxyPostAsync(string relativePath)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            var response = await client.PostAsync(BuildServiceUrl(relativePath), null);
            var content = await response.Content.ReadAsStringAsync();

            return new ContentResult
            {
                StatusCode = (int)response.StatusCode,
                Content = content,
                ContentType = "application/json"
            };
        }
        catch (Exception ex)
        {
            return StatusCode(503, new { message = $"Khong the ket noi toi Face camera service: {ex.Message}" });
        }
    }

    private async Task<IActionResult> ProxyPostJsonAsync<TRequest>(string relativePath, TRequest request)
    {
        try
        {
            var client = _httpClientFactory.CreateClient();
            var response = await client.PostAsJsonAsync(BuildServiceUrl(relativePath), request);
            var content = await response.Content.ReadAsStringAsync();

            return new ContentResult
            {
                StatusCode = (int)response.StatusCode,
                Content = content,
                ContentType = "application/json"
            };
        }
        catch (Exception ex)
        {
            return StatusCode(503, new { message = $"Khong the ket noi toi Face camera service: {ex.Message}" });
        }
    }

    private string BuildServiceUrl(string relativePath) => $"{_serviceBaseUrl}{relativePath}";

    private static string ResolveServiceBaseUrl(string? configuredValue, string fallbackValue) =>
        (configuredValue ?? fallbackValue).Trim().TrimEnd('/');

    public sealed class CameraOnRequest
    {
        public string Ip { get; set; } = string.Empty;
    }
}

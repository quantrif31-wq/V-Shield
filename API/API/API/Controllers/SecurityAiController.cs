using System.Diagnostics;
using System.Globalization;
using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using API.Data;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[Route("api/[controller]")]
[ApiController]
public class SecurityAiController : ControllerBase
{
    private static readonly object ProcessLock = new();
    private static readonly StringBuilder ProcessLogBuffer = new();
    private static readonly Regex AlertFileRegex =
        new(@"^(?<ts>\d{8}_\d{6})_id(?<track>-?\d+)_(?<label>.+)\.(?<ext>jpg|jpeg|png)$",
            RegexOptions.Compiled | RegexOptions.IgnoreCase);
    private const int MaxLogBufferLength = 24000;

    private static Process? _securityAiProcess;
    private static DateTimeOffset? _startedAtUtc;
    private static int? _activeCameraId;
    private static string? _activeSource;

    private readonly ApplicationDbContext _context;
    private readonly IConfiguration _configuration;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly string _serviceBaseUrl;

    public SecurityAiController(
        ApplicationDbContext context,
        IConfiguration configuration,
        IHttpClientFactory httpClientFactory)
    {
        _context = context;
        _configuration = configuration;
        _httpClientFactory = httpClientFactory;
        _serviceBaseUrl = ResolveServiceBaseUrl(
            configuration["AiServices:SecurityAiBaseUrl"],
            "http://127.0.0.1:5003"
        );
    }

    [HttpGet("status")]
    public async Task<IActionResult> GetStatus()
    {
        var remoteStatus = await SendServiceAsync(HttpMethod.Get, "/api/camera/status", timeoutMs: 4000);
        lock (ProcessLock)
        {
            return Ok(new { status = BuildStatusLocked(remoteStatus) });
        }
    }

    [HttpPost("start")]
    public async Task<IActionResult> Start([FromBody] StartSecurityAiRequest? request)
    {
        request ??= new StartSecurityAiRequest();

        var (source, cameraId, resolveError) = await ResolveSourceAsync(request);
        if (!string.IsNullOrWhiteSpace(resolveError))
        {
            return BadRequest(new { message = resolveError });
        }

        var ensureService = await EnsureServiceAvailableAsync();
        if (!ensureService.ok)
        {
            var statusFallback = await BuildStatusSnapshotForResponseAsync();
            return StatusCode(503, new
            {
                message = ensureService.error,
                status = statusFallback
            });
        }

        var cameraOnTimeoutMs = ResolveSecurityAiCameraOnTimeoutMs();
        var onResponse = await SendServiceAsync(
            HttpMethod.Post,
            "/api/camera/on",
            new
            {
                source,
                ip = source,
                restartIfRunning = request.RestartIfRunning.GetValueOrDefault(true),
                loopVideo = request.LoopVideo,
            },
            timeoutMs: cameraOnTimeoutMs
        );

        if (!onResponse.IsTransportSuccess)
        {
            var statusFallback = await BuildStatusSnapshotForResponseAsync();
            return StatusCode(503, new
            {
                message = $"Khong the ket noi Security AI service: {onResponse.ErrorMessage}",
                status = statusFallback
            });
        }

        if (onResponse.StatusCode >= 400)
        {
            if (onResponse.IsJson)
            {
                return new ContentResult
                {
                    StatusCode = onResponse.StatusCode,
                    Content = onResponse.TextBody,
                    ContentType = "application/json"
                };
            }

            return StatusCode(onResponse.StatusCode, new
            {
                message = "Security AI service tra ve loi khi bat camera.",
                detail = onResponse.TextBody
            });
        }

        lock (ProcessLock)
        {
            _activeCameraId = cameraId;
            _activeSource = source;
            if (_startedAtUtc == null)
            {
                _startedAtUtc = DateTimeOffset.UtcNow;
            }
            AppendProcessLogLocked($"[START] Camera source requested: {source}");
        }

        var statusPayload = await BuildStatusSnapshotForResponseAsync();
        var responseMessage = ExtractMessage(onResponse.JsonRoot) ?? "Da khoi dong AI an ninh.";

        return Ok(new
        {
            message = responseMessage,
            status = statusPayload
        });
    }

    [HttpPost("stop")]
    public async Task<IActionResult> Stop()
    {
        var remoteStop = await SendServiceAsync(HttpMethod.Post, "/api/camera/off", timeoutMs: 15000);

        lock (ProcessLock)
        {
            // Soft stop only: keep Python process alive for fast restart.
            _activeCameraId = null;
            _activeSource = null;
            _startedAtUtc = null;
            AppendProcessLogLocked("[STOP] Camera stream stopped. Security AI process kept alive.");
        }

        if (remoteStop.IsTransportSuccess && remoteStop.StatusCode < 400)
        {
            var statusSnapshot = await BuildStatusSnapshotForResponseAsync();
            return Ok(new
            {
                message = ExtractMessage(remoteStop.JsonRoot) ?? "Da dung luong AI an ninh. Service van dang san sang.",
                status = statusSnapshot
            });
        }

        // Keep UI responsive even when remote service has no valid response.
        var fallbackStatus = await BuildStatusSnapshotForResponseAsync();
        return Ok(new
        {
            message = "Da gui lenh dung luong AI an ninh.",
            warning = remoteStop.IsTransportSuccess
                ? "Khong nhan duoc phan hoi hop le tu Security AI service."
                : $"Khong the ket noi Security AI service: {remoteStop.ErrorMessage}",
            status = fallbackStatus
        });
    }

    [HttpPost("reset")]
    public async Task<IActionResult> Reset()
    {
        var remoteReset = await SendServiceAsync(HttpMethod.Post, "/api/camera/reset", timeoutMs: 12000);
        if (!remoteReset.IsTransportSuccess)
        {
            return StatusCode(503, new { message = $"Khong the ket noi Security AI service: {remoteReset.ErrorMessage}" });
        }

        if (remoteReset.StatusCode >= 400)
        {
            if (remoteReset.IsJson)
            {
                return new ContentResult
                {
                    StatusCode = remoteReset.StatusCode,
                    Content = remoteReset.TextBody,
                    ContentType = "application/json"
                };
            }

            return StatusCode(remoteReset.StatusCode, new
            {
                message = "Security AI service tra ve loi khi reset.",
                detail = remoteReset.TextBody
            });
        }

        var statusAfterReset = await BuildStatusSnapshotForResponseAsync();
        return Ok(new
        {
            message = ExtractMessage(remoteReset.JsonRoot) ?? "Da reset trang thai AI an ninh.",
            status = statusAfterReset
        });
    }

    [HttpPost("seek")]
    public async Task<IActionResult> Seek([FromBody] SeekSecurityAiRequest? request)
    {
        var frameIndex = request?.FrameIndex;
        if (frameIndex == null || frameIndex < 0)
        {
            return BadRequest(new { message = "FrameIndex khong hop le." });
        }

        var remoteSeek = await SendServiceAsync(
            HttpMethod.Post,
            "/api/camera/seek",
            new { frameIndex = frameIndex.Value },
            timeoutMs: 12000
        );

        if (!remoteSeek.IsTransportSuccess)
        {
            return StatusCode(503, new { message = $"Khong the ket noi Security AI service: {remoteSeek.ErrorMessage}" });
        }

        if (remoteSeek.StatusCode >= 400)
        {
            if (remoteSeek.IsJson)
            {
                return new ContentResult
                {
                    StatusCode = remoteSeek.StatusCode,
                    Content = remoteSeek.TextBody,
                    ContentType = "application/json"
                };
            }

            return StatusCode(remoteSeek.StatusCode, new
            {
                message = "Security AI service tra ve loi khi tua video.",
                detail = remoteSeek.TextBody
            });
        }

        var statusSnapshot = await BuildStatusSnapshotForResponseAsync();
        return Ok(new
        {
            message = ExtractMessage(remoteSeek.JsonRoot) ?? $"Da tua den frame {frameIndex.Value}.",
            frameIndex = frameIndex.Value,
            status = statusSnapshot
        });
    }

    [HttpGet("camera/status")]
    public Task<IActionResult> GetCameraStatus() =>
        ProxyJsonAsync("/api/camera/status", timeoutMs: 8000);

    [HttpGet("result")]
    [HttpGet("camera/result")]
    public Task<IActionResult> GetCameraResult() =>
        ProxyJsonAsync("/api/camera/result", timeoutMs: 12000, softenErrors: true);

    [HttpGet("camera/frame")]
    public async Task<IActionResult> GetCameraFrame()
    {
        var response = await SendServiceAsync(HttpMethod.Get, "/api/camera/frame", timeoutMs: 12000);
        if (!response.IsTransportSuccess)
        {
            return StatusCode(503, new { message = $"Khong the ket noi Security AI service: {response.ErrorMessage}" });
        }

        if (response.StatusCode >= 400)
        {
            if (response.IsJson)
            {
                return new ContentResult
                {
                    StatusCode = response.StatusCode,
                    Content = response.TextBody,
                    ContentType = "application/json"
                };
            }

            return StatusCode(response.StatusCode, new
            {
                message = "Security AI service tra ve loi khi lay frame.",
                detail = response.TextBody
            });
        }

        var contentType = string.IsNullOrWhiteSpace(response.ContentType)
            ? "image/jpeg"
            : response.ContentType;

        return File(response.Body, contentType);
    }

    [HttpGet("alerts")]
    public async Task<IActionResult> GetAlerts([FromQuery] int take = 24)
    {
        take = Math.Clamp(take, 1, 120);

        var remoteAlerts = await SendServiceAsync(HttpMethod.Get, $"/api/camera/alerts?take={take}", timeoutMs: 12000);
        if (remoteAlerts.IsTransportSuccess && remoteAlerts.StatusCode < 400 && remoteAlerts.IsJson)
        {
            if (remoteAlerts.JsonRoot.HasValue &&
                remoteAlerts.JsonRoot.Value.ValueKind == JsonValueKind.Object &&
                TryGetProperty(remoteAlerts.JsonRoot.Value, "items", out var itemsNode) &&
                itemsNode.ValueKind == JsonValueKind.Array)
            {
                var normalizedItems = itemsNode.EnumerateArray()
                    .Select(NormalizeRemoteAlertItem)
                    .ToList();

                var total = normalizedItems.Count;
                if (TryGetProperty(remoteAlerts.JsonRoot.Value, "total", out var totalNode) &&
                    totalNode.ValueKind == JsonValueKind.Number &&
                    totalNode.TryGetInt32(out var parsedTotal))
                {
                    total = parsedTotal;
                }

                return Ok(new
                {
                    items = normalizedItems,
                    total
                });
            }

            return new ContentResult
            {
                StatusCode = 200,
                Content = remoteAlerts.TextBody,
                ContentType = "application/json"
            };
        }

        // Fallback: Ä‘á»c trá»±c tiáº¿p tá»« thÆ° má»¥c alerts náº¿u service chÆ°a pháº£n há»“i.
        string alertsFolder;
        try
        {
            alertsFolder = ResolveAlertsFolder();
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = ex.Message });
        }

        if (!Directory.Exists(alertsFolder))
        {
            return Ok(new { items = Array.Empty<object>(), total = 0 });
        }

        var items = new DirectoryInfo(alertsFolder)
            .EnumerateFiles()
            .Where(IsSupportedAlertImage)
            .OrderByDescending(file => file.LastWriteTimeUtc)
            .Take(take)
            .Select(BuildAlertItem)
            .ToList();

        return Ok(new
        {
            items,
            total = items.Count
        });
    }

    [HttpGet("alerts/{fileName}")]
    public async Task<IActionResult> GetAlertImage(string fileName)
    {
        if (string.IsNullOrWhiteSpace(fileName))
        {
            return BadRequest(new { message = "Ten file khong hop le." });
        }

        var safeFileName = Path.GetFileName(fileName);
        if (!string.Equals(fileName, safeFileName, StringComparison.Ordinal))
        {
            return BadRequest(new { message = "Ten file khong hop le." });
        }

        var remoteImage = await SendServiceAsync(
            HttpMethod.Get,
            $"/api/camera/alerts/{Uri.EscapeDataString(safeFileName)}",
            timeoutMs: 12000
        );
        if (remoteImage.IsTransportSuccess && remoteImage.StatusCode < 400 && remoteImage.Body.Length > 0)
        {
            var remoteContentType = string.IsNullOrWhiteSpace(remoteImage.ContentType)
                ? GuessContentType(safeFileName)
                : remoteImage.ContentType;
            return File(remoteImage.Body, remoteContentType);
        }

        string alertsFolder;
        try
        {
            alertsFolder = ResolveAlertsFolder();
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = ex.Message });
        }

        var fullPath = Path.Combine(alertsFolder, safeFileName);
        if (!System.IO.File.Exists(fullPath))
        {
            return NotFound(new { message = "Khong tim thay anh canh bao." });
        }

        return PhysicalFile(fullPath, GuessContentType(safeFileName));
    }

    private async Task<IActionResult> ProxyJsonAsync(string relativePath, int timeoutMs, bool softenErrors = false)
    {
        var response = await SendServiceAsync(HttpMethod.Get, relativePath, timeoutMs: timeoutMs);
        if (!response.IsTransportSuccess)
        {
            if (softenErrors)
            {
                return Ok(new
                {
                    success = false,
                    running = false,
                    camera_enabled = false,
                    serviceReachable = false,
                    message = $"Khong the ket noi Security AI service: {response.ErrorMessage}"
                });
            }

            return StatusCode(503, new { message = $"Khong the ket noi Security AI service: {response.ErrorMessage}" });
        }

        if (softenErrors && response.StatusCode >= 400)
        {
            if (response.IsJson && response.JsonRoot.HasValue && response.JsonRoot.Value.ValueKind == JsonValueKind.Object)
            {
                var payload = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
                {
                    ["success"] = false,
                    ["running"] = false,
                    ["camera_enabled"] = false,
                    ["serviceReachable"] = true,
                    ["upstreamStatus"] = response.StatusCode
                };

                foreach (var property in response.JsonRoot.Value.EnumerateObject())
                {
                    payload[property.Name] = ConvertJsonValue(property.Value);
                }

                if (!payload.ContainsKey("message"))
                {
                    payload["message"] = "Security AI service tra ve loi khi lay du lieu.";
                }

                return Ok(payload);
            }

            return Ok(new
            {
                success = false,
                running = false,
                camera_enabled = false,
                serviceReachable = true,
                upstreamStatus = response.StatusCode,
                message = "Security AI service tra ve loi khi lay du lieu.",
                detail = response.TextBody
            });
        }

        var contentType = response.IsJson
            ? "application/json"
            : string.IsNullOrWhiteSpace(response.ContentType)
                ? "text/plain"
                : response.ContentType;

        return new ContentResult
        {
            StatusCode = response.StatusCode,
            Content = response.TextBody,
            ContentType = contentType
        };
    }

    private async Task<(bool ok, string? error)> EnsureServiceAvailableAsync()
    {
        if (await IsServiceReachableAsync(timeoutMs: 3500))
        {
            return (true, null);
        }

        string aiFolder;
        string appScriptPath;
        string pythonExecutable;
        try
        {
            aiFolder = ResolveSecurityAiFolder();
            appScriptPath = ResolveEntryScript(aiFolder);
            pythonExecutable = ResolvePythonExecutable(aiFolder);
        }
        catch (Exception ex)
        {
            return (false, ex.Message);
        }

        lock (ProcessLock)
        {
            if (IsProcessRunningLocked())
            {
                AppendProcessLogLocked("[WARN] Security AI service probe failed while process is running. Restarting process.");
                StopProcessLocked();
            }

            var startError = StartProcessLocked(aiFolder, appScriptPath, pythonExecutable);
            if (!string.IsNullOrWhiteSpace(startError))
            {
                return (false, startError);
            }
        }

        var startupTimeoutSeconds = ResolveSecurityAiStartupTimeoutSeconds();
        var ready = await WaitForServiceReadyAsync(TimeSpan.FromSeconds(startupTimeoutSeconds));
        if (!ready)
        {
            return (false, $"Khong the khoi dong Security AI API service sau {startupTimeoutSeconds} giay.");
        }

        return (true, null);
    }

    private async Task<bool> WaitForServiceReadyAsync(TimeSpan timeout)
    {
        var started = DateTimeOffset.UtcNow;
        while (DateTimeOffset.UtcNow - started < timeout)
        {
            if (await IsServiceReachableAsync(timeoutMs: 3000))
            {
                return true;
            }
            await Task.Delay(500);
        }
        return false;
    }

    private async Task<bool> IsServiceReachableAsync(int timeoutMs)
    {
        var healthProbe = await SendServiceAsync(HttpMethod.Get, "/health", timeoutMs: timeoutMs);
        if (healthProbe.IsTransportSuccess && healthProbe.StatusCode > 0 && healthProbe.StatusCode < 500)
        {
            return true;
        }

        var statusProbe = await SendServiceAsync(HttpMethod.Get, "/api/camera/status", timeoutMs: timeoutMs);
        return statusProbe.IsTransportSuccess && statusProbe.StatusCode > 0 && statusProbe.StatusCode < 500;
    }

    private async Task<(string? source, int? cameraId, string? error)> ResolveSourceAsync(StartSecurityAiRequest request)
    {
        var directSource = request.Source?.Trim();
        if (!string.IsNullOrWhiteSpace(directSource))
        {
            return (directSource, request.CameraId, null);
        }

        if (!request.CameraId.HasValue)
        {
            return (null, null, "Can truyen cameraId hoac source de khoi dong AI an ninh.");
        }

        var camera = await _context.Cameras
            .AsNoTracking()
            .Where(item => item.CameraId == request.CameraId.Value)
            .Select(item => new
            {
                item.CameraId,
                item.StreamUrl
            })
            .FirstOrDefaultAsync();

        if (camera == null)
        {
            return (null, null, $"Khong tim thay camera ID {request.CameraId.Value}.");
        }

        var streamUrl = camera.StreamUrl?.Trim();
        if (string.IsNullOrWhiteSpace(streamUrl))
        {
            return (null, camera.CameraId, $"Camera ID {camera.CameraId} chua co StreamUrl.");
        }

        return (streamUrl, camera.CameraId, null);
    }

    private async Task<object> BuildStatusSnapshotForResponseAsync()
    {
        var remote = await SendServiceAsync(HttpMethod.Get, "/api/camera/status", timeoutMs: 2500);
        lock (ProcessLock)
        {
            return BuildStatusLocked(remote);
        }
    }

    private object BuildStatusLocked(ServiceProxyResult remoteStatus)
    {
        var processRunning = IsProcessRunningLocked();
        var process = _securityAiProcess;
        bool? remoteRunning = null;
        bool hasRemoteSource = false;
        string? remoteSource = null;
        bool hasRemoteCameraId = false;
        int? remoteCameraId = null;

        var status = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
        {
            ["running"] = processRunning,
            ["pid"] = processRunning && process != null ? process.Id : (int?)null,
            ["source"] = _activeSource,
            ["cameraId"] = _activeCameraId,
            ["startedAtUtc"] = _startedAtUtc?.ToString("o"),
            ["recentLogs"] = GetRecentLogsLocked(),
            ["serviceBaseUrl"] = _serviceBaseUrl,
            ["serviceReachable"] = remoteStatus.IsTransportSuccess
        };

        if (remoteStatus.IsTransportSuccess)
        {
            status["serviceStatusCode"] = remoteStatus.StatusCode;
            if (remoteStatus.IsJson && remoteStatus.JsonRoot.HasValue && remoteStatus.JsonRoot.Value.ValueKind == JsonValueKind.Object)
            {
                var remoteJson = remoteStatus.JsonRoot.Value;
                foreach (var property in remoteJson.EnumerateObject())
                {
                    status[property.Name] = ConvertJsonValue(property.Value);
                }

                remoteRunning = TryGetBoolOrNull(remoteJson, "camera_enabled")
                    ?? TryGetBoolOrNull(remoteJson, "running");

                hasRemoteSource =
                    TryGetProperty(remoteJson, "source", out _) ||
                    TryGetProperty(remoteJson, "ip", out _);
                if (hasRemoteSource)
                {
                    remoteSource = TryGetString(remoteJson, "source")
                        ?? TryGetString(remoteJson, "ip")
                        ?? string.Empty;
                }

                hasRemoteCameraId =
                    TryGetProperty(remoteJson, "cameraId", out _) ||
                    TryGetProperty(remoteJson, "camera_id", out _);
                if (hasRemoteCameraId)
                {
                    remoteCameraId = TryGetIntOrNull(remoteJson, "cameraId")
                        ?? TryGetIntOrNull(remoteJson, "camera_id");
                }
            }
            else if (!string.IsNullOrWhiteSpace(remoteStatus.TextBody))
            {
                status["serviceRawBody"] = remoteStatus.TextBody;
            }
        }
        else
        {
            status["serviceError"] = remoteStatus.ErrorMessage;
        }

        var effectiveRunning = remoteRunning ?? processRunning;
        status["running"] = effectiveRunning;
        status["pid"] = effectiveRunning && processRunning && process != null ? process.Id : (int?)null;

        if (hasRemoteSource)
        {
            status["source"] = remoteSource ?? string.Empty;
            _activeSource = string.IsNullOrWhiteSpace(remoteSource) ? null : remoteSource;
        }
        else if (string.IsNullOrWhiteSpace(_activeSource) && status["source"] is string currentSource && !string.IsNullOrWhiteSpace(currentSource))
        {
            _activeSource = currentSource;
        }

        if (hasRemoteCameraId)
        {
            status["cameraId"] = remoteCameraId;
            _activeCameraId = remoteCameraId;
        }
        else if (_activeCameraId == null && status["cameraId"] is long cameraIdLong)
        {
            _activeCameraId = (int)cameraIdLong;
        }

        if (remoteRunning == false)
        {
            status["pid"] = null;
            status["source"] = hasRemoteSource ? (remoteSource ?? string.Empty) : string.Empty;
            status["cameraId"] = null;
            _activeSource = null;
            _activeCameraId = null;
        }

        return status;
    }

    private static bool TryGetProperty(JsonElement root, string name, out JsonElement value)
    {
        if (root.ValueKind != JsonValueKind.Object)
        {
            value = default;
            return false;
        }

        foreach (var prop in root.EnumerateObject())
        {
            if (string.Equals(prop.Name, name, StringComparison.OrdinalIgnoreCase))
            {
                value = prop.Value;
                return true;
            }
        }

        value = default;
        return false;
    }

    private static bool? TryGetBoolOrNull(JsonElement root, string name)
    {
        if (!TryGetProperty(root, name, out var value))
        {
            return null;
        }

        return value.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Number when value.TryGetInt64(out var number) => number != 0,
            JsonValueKind.String when bool.TryParse(value.GetString(), out var parsed) => parsed,
            JsonValueKind.String when long.TryParse(value.GetString(), out var parsedNumber) => parsedNumber != 0,
            JsonValueKind.Null => null,
            _ => null
        };
    }

    private static int? TryGetIntOrNull(JsonElement root, string name)
    {
        if (!TryGetProperty(root, name, out var value))
        {
            return null;
        }

        return value.ValueKind switch
        {
            JsonValueKind.Number when value.TryGetInt32(out var intValue) => intValue,
            JsonValueKind.Number when value.TryGetInt64(out var longValue) => (int)longValue,
            JsonValueKind.String when int.TryParse(value.GetString(), out var parsed) => parsed,
            JsonValueKind.String when long.TryParse(value.GetString(), out var parsedLong) => (int)parsedLong,
            _ => null
        };
    }

    private static string? TryGetString(JsonElement root, string name)
    {
        if (!TryGetProperty(root, name, out var value))
        {
            return null;
        }

        return value.ValueKind switch
        {
            JsonValueKind.String => value.GetString(),
            JsonValueKind.Number => value.ToString(),
            JsonValueKind.True => "true",
            JsonValueKind.False => "false",
            _ => null
        };
    }

    private static object? ConvertJsonValue(JsonElement value)
    {
        return value.ValueKind switch
        {
            JsonValueKind.Null => null,
            JsonValueKind.String => value.GetString(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Number => value.TryGetInt64(out var intNumber)
                ? intNumber
                : value.TryGetDouble(out var doubleNumber)
                    ? doubleNumber
                    : value.ToString(),
            JsonValueKind.Array => value.EnumerateArray().Select(ConvertJsonValue).ToList(),
            JsonValueKind.Object => value.EnumerateObject()
                .ToDictionary(property => property.Name, property => ConvertJsonValue(property.Value)),
            _ => value.ToString()
        };
    }

    private static string? ExtractMessage(JsonElement? root)
    {
        if (!root.HasValue || root.Value.ValueKind != JsonValueKind.Object)
        {
            return null;
        }

        return TryGetString(root.Value, "message")
            ?? TryGetString(root.Value, "status")
            ?? TryGetString(root.Value, "detail");
    }

    private object NormalizeRemoteAlertItem(JsonElement item)
    {
        if (item.ValueKind != JsonValueKind.Object)
        {
            return new { };
        }

        var fileName = TryGetString(item, "fileName")
            ?? TryGetString(item, "file_name")
            ?? string.Empty;

        var label = TryGetString(item, "label") ?? "ALERT";
        var capturedAt = TryGetString(item, "capturedAt")
            ?? TryGetString(item, "captured_at");

        object? trackId = null;
        if (TryGetProperty(item, "trackId", out var trackNode) ||
            TryGetProperty(item, "track_id", out trackNode))
        {
            trackId = ConvertJsonValue(trackNode);
        }

        object? sizeBytes = null;
        if (TryGetProperty(item, "sizeBytes", out var sizeNode) ||
            TryGetProperty(item, "size_bytes", out sizeNode))
        {
            sizeBytes = ConvertJsonValue(sizeNode);
        }

        var imageUrl = string.IsNullOrWhiteSpace(fileName)
            ? TryGetString(item, "imageUrl") ?? TryGetString(item, "image_url")
            : Url.ActionLink(
                action: nameof(GetAlertImage),
                controller: "SecurityAi",
                values: new { fileName },
                protocol: Request.Scheme,
                host: Request.Host.ToString());

        return new
        {
            fileName,
            label,
            trackId,
            capturedAt,
            imageUrl,
            sizeBytes
        };
    }

    private string? StartProcessLocked(string aiFolder, string appScriptPath, string pythonExecutable)
    {
        try
        {
            var processStartInfo = new ProcessStartInfo
            {
                FileName = pythonExecutable,
                WorkingDirectory = aiFolder,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            processStartInfo.Environment["PYTHONUNBUFFERED"] = "1";
            processStartInfo.Environment["SECURITY_AI_HEADLESS"] = "1";
            if (Uri.TryCreate(_serviceBaseUrl, UriKind.Absolute, out var serviceUri))
            {
                processStartInfo.Environment["SECURITY_AI_API_HOST"] = serviceUri.Host;
                processStartInfo.Environment["SECURITY_AI_API_PORT"] = serviceUri.Port.ToString(CultureInfo.InvariantCulture);
            }
            processStartInfo.ArgumentList.Add(appScriptPath);

            var process = Process.Start(processStartInfo);
            if (process == null)
            {
                return "Khong the khoi dong tien trinh AI an ninh.";
            }

            process.EnableRaisingEvents = true;
            process.OutputDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                {
                    lock (ProcessLock)
                    {
                        AppendProcessLogLocked($"[OUT] {e.Data}");
                    }
                }
            };
            process.ErrorDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                {
                    lock (ProcessLock)
                    {
                        AppendProcessLogLocked($"[ERR] {e.Data}");
                    }
                }
            };
            process.Exited += (_, _) =>
            {
                lock (ProcessLock)
                {
                    if (_securityAiProcess == null || _securityAiProcess.Id != process.Id)
                    {
                        return;
                    }

                    AppendProcessLogLocked($"[EXIT] Security AI process exited with code {process.ExitCode}.");
                    process.Dispose();
                    _securityAiProcess = null;
                    _startedAtUtc = null;
                    _activeCameraId = null;
                    _activeSource = null;
                }
            };

            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            _securityAiProcess = process;
            _startedAtUtc = DateTimeOffset.UtcNow;
            AppendProcessLogLocked("[START] Security AI process started.");
            return null;
        }
        catch (Exception ex)
        {
            return $"Khong the khoi dong tien trinh AI an ninh: {ex.Message}";
        }
    }

    private static bool IsProcessRunningLocked() =>
        _securityAiProcess != null && !_securityAiProcess.HasExited;

    private void StopProcessLocked()
    {
        if (_securityAiProcess == null)
        {
            _startedAtUtc = null;
            _activeCameraId = null;
            _activeSource = null;
            return;
        }

        try
        {
            if (!_securityAiProcess.HasExited)
            {
                _securityAiProcess.Kill(true);
                _securityAiProcess.WaitForExit(3000);
            }
        }
        catch (Exception ex)
        {
            AppendProcessLogLocked($"[ERR] Stop failed: {ex.Message}");
        }
        finally
        {
            _securityAiProcess.Dispose();
            _securityAiProcess = null;
            _startedAtUtc = null;
            _activeCameraId = null;
            _activeSource = null;
            AppendProcessLogLocked("[STOP] Security AI process stopped.");
        }
    }

    private static void AppendProcessLogLocked(string text)
    {
        ProcessLogBuffer.AppendLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {text}");
        if (ProcessLogBuffer.Length <= MaxLogBufferLength)
        {
            return;
        }

        ProcessLogBuffer.Remove(0, ProcessLogBuffer.Length - MaxLogBufferLength);
    }

    private static string GetRecentLogsLocked()
    {
        var logs = ProcessLogBuffer.ToString();
        return logs.Length <= 3000 ? logs : logs[^3000..];
    }

    private async Task<ServiceProxyResult> SendServiceAsync(
        HttpMethod method,
        string relativePath,
        object? payload = null,
        int timeoutMs = 10000)
    {
        try
        {
            using var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromMilliseconds(Math.Max(1000, timeoutMs));

            using var request = new HttpRequestMessage(method, BuildServiceUrl(relativePath));
            if (payload != null)
            {
                request.Content = JsonContent.Create(payload);
            }

            using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);
            var body = await response.Content.ReadAsByteArrayAsync();
            var contentType = response.Content.Headers.ContentType?.MediaType ?? string.Empty;
            var textBody = body.Length == 0 ? string.Empty : Encoding.UTF8.GetString(body);

            JsonElement? jsonRoot = null;
            if (!string.IsNullOrWhiteSpace(textBody) &&
                (contentType.Contains("json", StringComparison.OrdinalIgnoreCase) ||
                 textBody.TrimStart().StartsWith("{", StringComparison.Ordinal) ||
                 textBody.TrimStart().StartsWith("[", StringComparison.Ordinal)))
            {
                try
                {
                    using var doc = JsonDocument.Parse(textBody);
                    jsonRoot = doc.RootElement.Clone();
                }
                catch
                {
                    // ignored
                }
            }

            return new ServiceProxyResult
            {
                IsTransportSuccess = true,
                StatusCode = (int)response.StatusCode,
                Body = body,
                TextBody = textBody,
                ContentType = contentType,
                JsonRoot = jsonRoot
            };
        }
        catch (Exception ex)
        {
            return new ServiceProxyResult
            {
                IsTransportSuccess = false,
                StatusCode = 0,
                Body = Array.Empty<byte>(),
                TextBody = string.Empty,
                ContentType = string.Empty,
                JsonRoot = null,
                ErrorMessage = BuildExceptionMessage(ex)
            };
        }
    }

    private static string BuildExceptionMessage(Exception exception)
    {
        var messages = new List<string>();
        var current = exception;
        while (current != null)
        {
            if (!string.IsNullOrWhiteSpace(current.Message))
            {
                messages.Add(current.Message.Trim());
            }
            current = current.InnerException;
        }

        return messages.Count == 0 ? "Unknown transport error." : string.Join(" | ", messages.Distinct());
    }

    private string BuildServiceUrl(string relativePath)
    {
        var normalizedPath = relativePath.StartsWith("/", StringComparison.Ordinal)
            ? relativePath
            : "/" + relativePath;
        return $"{_serviceBaseUrl}{normalizedPath}";
    }

    private string ResolveSecurityAiFolder()
    {
        var configuredFolder = _configuration["AiServices:SecurityAiFolder"]?.Trim();
        if (!string.IsNullOrWhiteSpace(configuredFolder))
        {
            var normalizedConfiguredPath = Path.GetFullPath(configuredFolder);
            if (!Directory.Exists(normalizedConfiguredPath))
            {
                throw new DirectoryNotFoundException($"Khong tim thay thu muc AI_An_Ninh: {normalizedConfiguredPath}");
            }

            return normalizedConfiguredPath;
        }

        var candidates = new[]
        {
            Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "AI_Project", "AI_An_Ninh")),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "AI_Project", "AI_An_Ninh")),
            Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), "AI_Project", "AI_An_Ninh"))
        };

        return candidates.FirstOrDefault(Directory.Exists) ?? candidates[0];
    }

    private string ResolveEntryScript(string aiFolder)
    {
        var configuredScript = _configuration["AiServices:SecurityAiEntryScript"]?.Trim();
        if (!string.IsNullOrWhiteSpace(configuredScript))
        {
            var absoluteScriptPath = Path.IsPathRooted(configuredScript)
                ? configuredScript
                : Path.Combine(aiFolder, configuredScript);

            if (!System.IO.File.Exists(absoluteScriptPath))
            {
                throw new FileNotFoundException($"Khong tim thay script AI an ninh: {absoluteScriptPath}");
            }

            return absoluteScriptPath;
        }

        var defaultScript = Path.Combine(aiFolder, "app.py");
        if (!System.IO.File.Exists(defaultScript))
        {
            throw new FileNotFoundException($"Khong tim thay file app.py tai {defaultScript}");
        }

        return defaultScript;
    }

    private string ResolvePythonExecutable(string aiFolder)
    {
        var configuredPythonExecutable = _configuration["AiServices:SecurityAiPythonExe"]?.Trim();
        var candidates = new List<string>();
        if (!string.IsNullOrWhiteSpace(configuredPythonExecutable))
        {
            if (Path.IsPathRooted(configuredPythonExecutable))
            {
                candidates.Add(configuredPythonExecutable);
            }
            else
            {
                var candidatePath = Path.GetFullPath(Path.Combine(aiFolder, configuredPythonExecutable));
                candidates.Add(candidatePath);
                candidates.Add(configuredPythonExecutable);
            }
        }

        if (OperatingSystem.IsWindows())
        {
            candidates.AddRange(new[]
            {
                Path.Combine(aiFolder, "venv", "Scripts", "python.exe"),
                Path.Combine(aiFolder, ".venv", "Scripts", "python.exe"),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "doc_bien_gpu", "venv", "Scripts", "python.exe")),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "face_recognition", "venv", "Scripts", "python.exe")),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "QR_Dong", "venv", "Scripts", "python.exe"))
            });
        }
        else
        {
            candidates.AddRange(new[]
            {
                Path.Combine(aiFolder, "venv", "bin", "python"),
                Path.Combine(aiFolder, ".venv", "bin", "python"),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "doc_bien_gpu", "venv", "bin", "python")),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "face_recognition", "venv", "bin", "python")),
                Path.GetFullPath(Path.Combine(aiFolder, "..", "QR_Dong", "venv", "bin", "python"))
            });
        }

        var userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (!string.IsNullOrWhiteSpace(userProfile))
        {
            if (OperatingSystem.IsWindows())
            {
                candidates.Add(Path.Combine(userProfile, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python.exe"));
            }
            else
            {
                candidates.Add(Path.Combine(userProfile, ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "python", "python"));
            }
        }

        if (OperatingSystem.IsWindows())
        {
            candidates.AddRange(new[] { "python", "py" });
        }
        else
        {
            candidates.AddRange(new[] { "python3", "python" });
        }

        foreach (var candidate in candidates
            .Where(static value => !string.IsNullOrWhiteSpace(value))
            .Select(static value => value.Trim())
            .Distinct(StringComparer.OrdinalIgnoreCase))
        {
            if (Path.IsPathRooted(candidate) && !System.IO.File.Exists(candidate))
            {
                continue;
            }

            if (IsUsablePythonExecutable(candidate))
            {
                return candidate;
            }
        }

        var previewCandidates = string.Join("; ", candidates
            .Where(static value => !string.IsNullOrWhiteSpace(value))
            .Take(8));
        throw new FileNotFoundException(
            $"Khong tim thay Python hop le de chay Security AI. Da thu cac candidate: {previewCandidates}");
    }

    private static bool IsUsablePythonExecutable(string commandOrPath)
    {
        try
        {
            var processStartInfo = new ProcessStartInfo
            {
                FileName = commandOrPath,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };
            processStartInfo.ArgumentList.Add("--version");

            using var process = Process.Start(processStartInfo);
            if (process == null)
            {
                return false;
            }

            if (!process.WaitForExit(3000))
            {
                try
                {
                    process.Kill(entireProcessTree: true);
                }
                catch
                {
                    // ignored
                }

                return false;
            }

            return process.ExitCode == 0;
        }
        catch
        {
            return false;
        }
    }

    private string ResolveAlertsFolder()
    {
        var configuredAlertsFolder = _configuration["AiServices:SecurityAiAlertsFolder"]?.Trim();
        if (!string.IsNullOrWhiteSpace(configuredAlertsFolder))
        {
            return Path.IsPathRooted(configuredAlertsFolder)
                ? configuredAlertsFolder
                : Path.GetFullPath(Path.Combine(ResolveSecurityAiFolder(), configuredAlertsFolder));
        }

        return Path.Combine(ResolveSecurityAiFolder(), "alerts");
    }

    private static bool IsSupportedAlertImage(FileInfo file)
    {
        var extension = file.Extension.ToLowerInvariant();
        return extension is ".jpg" or ".jpeg" or ".png";
    }

    private object BuildAlertItem(FileInfo file)
    {
        var (label, trackId, capturedAt) = ParseAlertMetadata(file);
        var imageUrl = Url.ActionLink(
            action: nameof(GetAlertImage),
            controller: "SecurityAi",
            values: new { fileName = file.Name },
            protocol: Request.Scheme,
            host: Request.Host.ToString()
        );

        return new
        {
            fileName = file.Name,
            label,
            trackId,
            capturedAt = capturedAt.ToString("o"),
            imageUrl,
            sizeBytes = file.Length
        };
    }

    private static (string label, int? trackId, DateTimeOffset capturedAt) ParseAlertMetadata(FileInfo file)
    {
        var defaultTimestamp = new DateTimeOffset(file.LastWriteTimeUtc, TimeSpan.Zero);
        var defaultLabel = "ALERT";
        int? defaultTrackId = null;

        var match = AlertFileRegex.Match(file.Name);
        if (!match.Success)
        {
            return (defaultLabel, defaultTrackId, defaultTimestamp);
        }

        var labelRaw = match.Groups["label"].Value;
        var normalizedLabel = string.IsNullOrWhiteSpace(labelRaw)
            ? defaultLabel
            : labelRaw.Replace('_', ' ').Trim().ToUpperInvariant();

        var trackText = match.Groups["track"].Value;
        var trackId = int.TryParse(trackText, out var parsedTrackId)
            ? parsedTrackId
            : defaultTrackId;

        var timestampText = match.Groups["ts"].Value;
        if (!DateTime.TryParseExact(
                timestampText,
                "yyyyMMdd_HHmmss",
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeLocal,
                out var localTimestamp))
        {
            return (normalizedLabel, trackId, defaultTimestamp);
        }

        return (normalizedLabel, trackId, new DateTimeOffset(localTimestamp));
    }

    private static string GuessContentType(string fileName)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        return extension switch
        {
            ".png" => "image/png",
            ".jpg" => "image/jpeg",
            ".jpeg" => "image/jpeg",
            _ => "application/octet-stream"
        };
    }

    private static string ResolveServiceBaseUrl(string? configuredValue, string fallbackValue) =>
        (configuredValue ?? fallbackValue).Trim().TrimEnd('/');

    private int ResolveSecurityAiStartupTimeoutSeconds()
    {
        const int defaultSeconds = 60;
        const int minSeconds = 20;
        const int maxSeconds = 240;

        var configured = _configuration["AiServices:SecurityAiStartupTimeoutSeconds"];
        if (!int.TryParse(configured, out var parsed))
        {
            return defaultSeconds;
        }

        return Math.Clamp(parsed, minSeconds, maxSeconds);
    }

    private int ResolveSecurityAiCameraOnTimeoutMs()
    {
        const int defaultMs = 45000;
        const int minMs = 5000;
        const int maxMs = 120000;

        var configured = _configuration["AiServices:SecurityAiCameraOnTimeoutMs"];
        if (!int.TryParse(configured, out var parsed))
        {
            return defaultMs;
        }

        return Math.Clamp(parsed, minMs, maxMs);
    }

    private sealed class ServiceProxyResult
    {
        public bool IsTransportSuccess { get; set; }
        public int StatusCode { get; set; }
        public byte[] Body { get; set; } = Array.Empty<byte>();
        public string TextBody { get; set; } = string.Empty;
        public string ContentType { get; set; } = string.Empty;
        public JsonElement? JsonRoot { get; set; }
        public string? ErrorMessage { get; set; }
        public bool IsJson => JsonRoot.HasValue;
    }

    public sealed class StartSecurityAiRequest
    {
        public int? CameraId { get; set; }
        public string? Source { get; set; }
        public bool? RestartIfRunning { get; set; }
        public bool? LoopVideo { get; set; }
    }

    public sealed class SeekSecurityAiRequest
    {
        public int? FrameIndex { get; set; }
    }
}


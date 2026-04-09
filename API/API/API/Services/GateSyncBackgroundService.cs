using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using API.Data;
using API.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace API.Services;

public sealed class GateSyncBackgroundService : BackgroundService
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    private readonly IServiceScopeFactory _scopeFactory;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IOptionsMonitor<GateSyncOptions> _optionsMonitor;
    private readonly ILogger<GateSyncBackgroundService> _logger;

    public GateSyncBackgroundService(
        IServiceScopeFactory scopeFactory,
        IHttpClientFactory httpClientFactory,
        IOptionsMonitor<GateSyncOptions> optionsMonitor,
        ILogger<GateSyncBackgroundService> logger)
    {
        _scopeFactory = scopeFactory;
        _httpClientFactory = httpClientFactory;
        _optionsMonitor = optionsMonitor;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var options = _optionsMonitor.CurrentValue;
            var delay = TimeSpan.FromSeconds(Math.Max(5, options.PollIntervalSeconds));

            if (!options.Enabled || string.IsNullOrWhiteSpace(options.RemoteBaseUrl))
            {
                await Task.Delay(delay, stoppingToken);
                continue;
            }

            try
            {
                await ProcessPendingSyncsAsync(options, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Gate sync background worker failed.");
            }

            await Task.Delay(delay, stoppingToken);
        }
    }

    private async Task ProcessPendingSyncsAsync(GateSyncOptions options, CancellationToken cancellationToken)
    {
        using var scope = _scopeFactory.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var nowUtc = DateTime.UtcNow;

        var pendingItems = await dbContext.PendingGateSyncs
            .Where(item =>
                (item.Status == "PENDING" || item.Status == "RETRY") &&
                item.SyncDueAt <= nowUtc)
            .OrderBy(item => item.SyncDueAt)
            .ThenBy(item => item.PendingGateSyncId)
            .Take(Math.Max(1, options.BatchSize))
            .ToListAsync(cancellationToken);

        if (pendingItems.Count == 0)
        {
            return;
        }

        foreach (var pendingItem in pendingItems)
        {
            await ProcessPendingItemAsync(dbContext, pendingItem, options, cancellationToken);
        }

        if (dbContext.ChangeTracker.HasChanges())
        {
            await dbContext.SaveChangesAsync(cancellationToken);
        }
    }

    private async Task ProcessPendingItemAsync(
        ApplicationDbContext dbContext,
        PendingGateSync pendingItem,
        GateSyncOptions options,
        CancellationToken cancellationToken)
    {
        var nowUtc = DateTime.UtcNow;
        pendingItem.LastAttemptAt = nowUtc;

        var accessLog = await dbContext.AccessLogs
            .FirstOrDefaultAsync(log => log.LogId == pendingItem.AccessLogId, cancellationToken);

        try
        {
            var client = _httpClientFactory.CreateClient(nameof(GateSyncBackgroundService));
            var endpoint = BuildEndpoint(options.RemoteBaseUrl, options.GateScanPath);

            var response = await client.PostAsJsonAsync(endpoint, new
            {
                licensePlate = pendingItem.LicensePlate,
                employeeId = pendingItem.EmployeeId,
                vehicleTypeId = pendingItem.VehicleTypeId,
                description = pendingItem.Description,
                gateId = pendingItem.GateId,
                cameraId = pendingItem.CameraId
            }, cancellationToken);

            var body = await response.Content.ReadAsStringAsync(cancellationToken);
            var remoteResponse = DeserializeResponse(body);
            var remoteMessage = remoteResponse?.Message;

            if (response.IsSuccessStatusCode && remoteResponse?.Success == true)
            {
                pendingItem.Status = "SYNCED";
                pendingItem.SyncedAt = nowUtc;
                pendingItem.RemoteMessage = Truncate(remoteMessage, 500);
                pendingItem.LastError = null;

                if (accessLog != null)
                {
                    accessLog.ResultStatus = "SYNCED";
                    accessLog.Note = AppendNote(accessLog.Note, $"Da doi chieu VPS: {remoteMessage}");
                }

                return;
            }

            var failureMessage = string.IsNullOrWhiteSpace(remoteMessage)
                ? (!string.IsNullOrWhiteSpace(body) ? body : $"VPS loi {(int)response.StatusCode}")
                : remoteMessage;

            if (ShouldRetry(response.StatusCode))
            {
                ScheduleRetry(pendingItem, options, failureMessage, accessLog);
                return;
            }

            MarkFailed(pendingItem, failureMessage, accessLog);
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            throw;
        }
        catch (Exception ex)
        {
            ScheduleRetry(pendingItem, options, ex.Message, accessLog);
        }
    }

    private static bool ShouldRetry(HttpStatusCode statusCode)
    {
        var numericStatusCode = (int)statusCode;
        return numericStatusCode >= 500 ||
               statusCode == HttpStatusCode.RequestTimeout ||
               statusCode == HttpStatusCode.BadGateway ||
               statusCode == HttpStatusCode.ServiceUnavailable ||
               statusCode == HttpStatusCode.GatewayTimeout;
    }

    private static void ScheduleRetry(
        PendingGateSync pendingItem,
        GateSyncOptions options,
        string? failureMessage,
        AccessLog? accessLog)
    {
        pendingItem.RetryCount += 1;
        pendingItem.LastError = Truncate(failureMessage, 500);

        if (pendingItem.RetryCount >= Math.Max(1, options.MaxRetryCount))
        {
            MarkFailed(pendingItem, failureMessage, accessLog);
            return;
        }

        pendingItem.Status = "RETRY";
        pendingItem.SyncDueAt = DateTime.UtcNow.AddSeconds(Math.Max(10, options.RetryDelaySeconds));

        if (accessLog != null)
        {
            accessLog.Note = AppendNote(accessLog.Note, $"Cho sync lai VPS lan {pendingItem.RetryCount}: {failureMessage}");
        }
    }

    private static void MarkFailed(PendingGateSync pendingItem, string? failureMessage, AccessLog? accessLog)
    {
        pendingItem.Status = "FAILED";
        pendingItem.LastError = Truncate(failureMessage, 500);

        if (accessLog != null)
        {
            accessLog.ResultStatus = "REMOTE_FAIL";
            accessLog.Note = AppendNote(accessLog.Note, $"Doi chieu VPS that bai: {failureMessage}");
        }
    }

    private static string BuildEndpoint(string baseUrl, string path)
    {
        var normalizedBaseUrl = baseUrl.Trim().TrimEnd('/');
        var normalizedPath = string.IsNullOrWhiteSpace(path) ? "api/Gate/scan" : path.Trim().TrimStart('/');
        return $"{normalizedBaseUrl}/{normalizedPath}";
    }

    private static GateSyncApiResponse? DeserializeResponse(string? body)
    {
        if (string.IsNullOrWhiteSpace(body))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<GateSyncApiResponse>(body, JsonOptions);
        }
        catch
        {
            return null;
        }
    }

    private static string? Truncate(string? value, int maxLength)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return value;
        }

        return value.Length <= maxLength ? value : value[..maxLength];
    }

    private static string AppendNote(string? currentNote, string noteToAppend)
    {
        var baseNote = string.IsNullOrWhiteSpace(currentNote)
            ? string.Empty
            : $"{currentNote.Trim()} | ";
        return Truncate($"{baseNote}{noteToAppend.Trim()}", 500) ?? string.Empty;
    }

    private sealed class GateSyncApiResponse
    {
        public bool Success { get; set; }
        public string? Message { get; set; }
    }
}

namespace API.Services;

public sealed class GateSyncOptions
{
    public bool Enabled { get; set; } = true;
    public string RemoteBaseUrl { get; set; } = string.Empty;
    public string GateScanPath { get; set; } = "/api/Gate/scan";
    public int SyncDelayMinutes { get; set; } = 3;
    public int PollIntervalSeconds { get; set; } = 30;
    public int RetryDelaySeconds { get; set; } = 60;
    public int BatchSize { get; set; } = 10;
    public int MaxRetryCount { get; set; } = 10;
}

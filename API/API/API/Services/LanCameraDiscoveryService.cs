using System.Collections.Concurrent;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Caching.Memory;

namespace API.Services;

public interface ILanCameraDiscoveryService
{
    Task<IReadOnlyList<IpWebcamCandidate>> DiscoverIpWebcamsAsync(CancellationToken cancellationToken = default);
}

public sealed class LanCameraDiscoveryService : ILanCameraDiscoveryService
{
    private static readonly int[] CommonPorts = [8080, 8081];
    private static readonly Regex TitleRegex = new("<title>(.*?)</title>", RegexOptions.IgnoreCase | RegexOptions.Singleline | RegexOptions.Compiled);
    private const int DiscoveryParallelism = 96;
    private const int PortProbeTimeoutMs = 120;
    private const int HttpProbeTimeoutMs = 650;
    private const int RootBodySnippetLength = 4096;

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IMemoryCache _cache;

    public LanCameraDiscoveryService(IHttpClientFactory httpClientFactory, IMemoryCache cache)
    {
        _httpClientFactory = httpClientFactory;
        _cache = cache;
    }

    public async Task<IReadOnlyList<IpWebcamCandidate>> DiscoverIpWebcamsAsync(CancellationToken cancellationToken = default)
    {
        const string cacheKey = "ip-webcam-discovery";
        if (_cache.TryGetValue(cacheKey, out IReadOnlyList<IpWebcamCandidate>? cached) &&
            cached is not null &&
            cached.Count > 0)
        {
            return cached;
        }

        var localIps = GetPrivateLocalIps();
        var subnetPrefixes = localIps
            .Select(ToSubnetPrefix)
            .Where(prefix => !string.IsNullOrWhiteSpace(prefix))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(prefix => prefix.StartsWith("192.168.137.", StringComparison.OrdinalIgnoreCase) ? 0 : 1)
            .ToArray();

        if (subnetPrefixes.Length == 0)
        {
            return Array.Empty<IpWebcamCandidate>();
        }

        var client = _httpClientFactory.CreateClient();
        client.Timeout = TimeSpan.FromMilliseconds(HttpProbeTimeoutMs);

        var results = new ConcurrentBag<IpWebcamCandidate>();
        using var semaphore = new SemaphoreSlim(DiscoveryParallelism);
        var probeTasks = new List<Task>();

        foreach (var subnetPrefix in subnetPrefixes)
        {
            for (var host = 1; host <= 254; host++)
            {
                var ip = $"{subnetPrefix}.{host}";
                if (localIps.Contains(ip))
                {
                    continue;
                }

                foreach (var port in CommonPorts)
                {
                    probeTasks.Add(ProbeIpWebcamAsync(client, semaphore, results, ip, port, cancellationToken));
                }
            }
        }

        await Task.WhenAll(probeTasks);

        var cameras = results
            .GroupBy(camera => $"{camera.IpAddress}:{camera.Port}", StringComparer.OrdinalIgnoreCase)
            .Select(group => group.First())
            .OrderBy(camera => camera.IpAddress, StringComparer.OrdinalIgnoreCase)
            .ThenBy(camera => camera.Port)
            .ToArray();

        if (cameras.Length > 0)
        {
            _cache.Set(cacheKey, cameras, TimeSpan.FromSeconds(10));
        }
        else
        {
            _cache.Remove(cacheKey);
        }

        return cameras;
    }

    private static HashSet<string> GetPrivateLocalIps()
    {
        var ips = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var networkInterface in NetworkInterface.GetAllNetworkInterfaces())
        {
            if (networkInterface.OperationalStatus != OperationalStatus.Up ||
                networkInterface.NetworkInterfaceType == NetworkInterfaceType.Loopback)
            {
                continue;
            }

            var ipProperties = networkInterface.GetIPProperties();
            var hasIpv4Gateway = ipProperties.GatewayAddresses.Any(gateway =>
                gateway?.Address is not null &&
                gateway.Address.AddressFamily == AddressFamily.InterNetwork &&
                !IPAddress.Any.Equals(gateway.Address) &&
                !IPAddress.None.Equals(gateway.Address));

            if (!hasIpv4Gateway && !LooksLikeHotspotInterface(networkInterface))
            {
                continue;
            }

            foreach (var address in ipProperties.UnicastAddresses)
            {
                if (address.Address.AddressFamily != AddressFamily.InterNetwork ||
                    IPAddress.IsLoopback(address.Address))
                {
                    continue;
                }

                var ip = address.Address.ToString();
                if (IsPrivateIpv4(ip))
                {
                    ips.Add(ip);
                }
            }
        }

        return ips;
    }

    private static bool LooksLikeHotspotInterface(NetworkInterface networkInterface)
    {
        var signature = $"{networkInterface.Name} {networkInterface.Description}";

        return signature.Contains("Local Area Connection*", StringComparison.OrdinalIgnoreCase) ||
               signature.Contains("Wi-Fi Direct", StringComparison.OrdinalIgnoreCase) ||
               signature.Contains("Mobile Hotspot", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsPrivateIpv4(string ip)
    {
        var parts = ip.Split('.');
        if (parts.Length != 4 ||
            !int.TryParse(parts[0], out var first) ||
            !int.TryParse(parts[1], out var second))
        {
            return false;
        }

        return first == 10 ||
               first == 192 && second == 168 ||
               first == 172 && second >= 16 && second <= 31;
    }

    private static string ToSubnetPrefix(string ip)
    {
        var parts = ip.Split('.');
        return parts.Length == 4 ? $"{parts[0]}.{parts[1]}.{parts[2]}" : string.Empty;
    }

    private static bool LooksLikeIpCameraLite(string body)
    {
        return body.Contains("IP Camera Lite", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("audio.opus", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("live.flv", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("RTSP Server Closed", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("Set to close camera when no client connected", StringComparison.OrdinalIgnoreCase);
    }

    private static string BuildDisplayName(string ip, string? title, string body)
    {
        if (LooksLikeIpCameraLite(body))
        {
            if (string.IsNullOrWhiteSpace(title) ||
                title.Contains("Server", StringComparison.OrdinalIgnoreCase) ||
                title.Contains("IP Camera", StringComparison.OrdinalIgnoreCase))
            {
                return $"IP Camera Lite {ip}";
            }

            return title.Trim();
        }

        if (string.IsNullOrWhiteSpace(title) || title.Contains("IP Webcam", StringComparison.OrdinalIgnoreCase))
        {
            return $"IP Webcam {ip}";
        }

        return title.Trim();
    }

    private static string? ExtractTitle(string html)
    {
        var match = TitleRegex.Match(html);
        if (!match.Success)
        {
            return null;
        }

        return WebUtility.HtmlDecode(match.Groups[1].Value).Trim();
    }

    private static bool LooksLikeIpWebcam(string body)
    {
        return body.Contains("IP Webcam", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("RTSP/h264/ONVIF", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("/videofeed", StringComparison.OrdinalIgnoreCase) ||
               body.Contains("browserfs.html", StringComparison.OrdinalIgnoreCase);
    }

    private static bool LooksLikeSupportedLanCamera(string body)
    {
        return LooksLikeIpWebcam(body) || LooksLikeIpCameraLite(body);
    }

    private static bool LooksLikePreviewContentType(string? contentType)
    {
        if (string.IsNullOrWhiteSpace(contentType))
        {
            return false;
        }

        return contentType.Contains("multipart/x-mixed-replace", StringComparison.OrdinalIgnoreCase) ||
               contentType.Contains("image/jpeg", StringComparison.OrdinalIgnoreCase) ||
               contentType.Contains("image/jpg", StringComparison.OrdinalIgnoreCase);
    }

    private static IReadOnlyList<string> BuildRtspUrls(string ip, int port, string body)
    {
        var candidates = new List<string>();
        void Add(string suffix)
        {
            var url = $"rtsp://{ip}:{port}/{suffix}";
            if (!candidates.Contains(url, StringComparer.OrdinalIgnoreCase))
            {
                candidates.Add(url);
            }
        }

        if (LooksLikeIpCameraLite(body) &&
            body.Contains("RTSP Server Closed", StringComparison.OrdinalIgnoreCase) &&
            !body.Contains(".sdp", StringComparison.OrdinalIgnoreCase))
        {
            return candidates;
        }

        if (body.Contains("h264.sdp", StringComparison.OrdinalIgnoreCase))
        {
            Add("h264.sdp");
        }

        if (body.Contains("h264_ulaw.sdp", StringComparison.OrdinalIgnoreCase))
        {
            Add("h264_ulaw.sdp");
        }

        if (body.Contains("h264_pcm.sdp", StringComparison.OrdinalIgnoreCase))
        {
            Add("h264_pcm.sdp");
        }

        if (LooksLikeIpWebcam(body))
        {
            Add("h264.sdp");
            Add("h264_ulaw.sdp");
            Add("h264_pcm.sdp");
        }

        return candidates;
    }

    private static IpWebcamCandidate BuildCandidate(string ip, int port, string body)
    {
        var baseUrl = $"http://{ip}:{port}";
        var isIpCameraLite = LooksLikeIpCameraLite(body);
        return new IpWebcamCandidate
        {
            Name = BuildDisplayName(ip, ExtractTitle(body), body),
            IpAddress = ip,
            Port = port,
            BaseUrl = baseUrl,
            PreviewUrl = isIpCameraLite ? $"{baseUrl}/video" : $"{baseUrl}/videofeed",
            SnapshotUrl = isIpCameraLite ? string.Empty : $"{baseUrl}/shot.jpg",
            RtspUrls = BuildRtspUrls(ip, port, body)
        };
    }

    private static IpWebcamCandidate BuildPreviewCandidate(string ip, int port, string previewPath)
    {
        var baseUrl = $"http://{ip}:{port}";
        var normalizedPreviewPath = previewPath.StartsWith('/') ? previewPath : $"/{previewPath}";
        var isIpCameraLite = normalizedPreviewPath.Equals("/video", StringComparison.OrdinalIgnoreCase);

        return new IpWebcamCandidate
        {
            Name = isIpCameraLite ? $"IP Camera Lite {ip}" : $"IP Webcam {ip}",
            IpAddress = ip,
            Port = port,
            BaseUrl = baseUrl,
            PreviewUrl = $"{baseUrl}{normalizedPreviewPath}",
            SnapshotUrl = isIpCameraLite ? string.Empty : $"{baseUrl}/shot.jpg",
            RtspUrls = Array.Empty<string>()
        };
    }

    private static async Task<bool> CanOpenPortAsync(string ip, int port, CancellationToken cancellationToken)
    {
        using var tcpClient = new TcpClient();
        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeoutCts.CancelAfter(TimeSpan.FromMilliseconds(PortProbeTimeoutMs));

        try
        {
            await tcpClient.ConnectAsync(ip, port, timeoutCts.Token);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private static async Task<string> ReadBodySnippetAsync(HttpContent content, CancellationToken cancellationToken)
    {
        await using var stream = await content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream, Encoding.UTF8, detectEncodingFromByteOrderMarks: true, bufferSize: RootBodySnippetLength, leaveOpen: false);
        var buffer = new char[RootBodySnippetLength];
        var read = await reader.ReadBlockAsync(buffer.AsMemory(0, buffer.Length), cancellationToken);
        return read <= 0 ? string.Empty : new string(buffer, 0, read);
    }

    private static async Task<IpWebcamCandidate?> ProbePreviewEndpointAsync(
        HttpClient client,
        string ip,
        int port,
        string previewPath,
        CancellationToken cancellationToken)
    {
        var previewUrl = $"http://{ip}:{port}{previewPath}";
        using var request = new HttpRequestMessage(HttpMethod.Get, previewUrl);
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            return null;
        }

        var contentType = response.Content.Headers.ContentType?.MediaType;
        if (!LooksLikePreviewContentType(contentType))
        {
            return null;
        }

        return BuildPreviewCandidate(ip, port, previewPath);
    }

    private async Task ProbeIpWebcamAsync(
        HttpClient client,
        SemaphoreSlim semaphore,
        ConcurrentBag<IpWebcamCandidate> results,
        string ip,
        int port,
        CancellationToken cancellationToken)
    {
        await semaphore.WaitAsync(cancellationToken);

        try
        {
            if (!await CanOpenPortAsync(ip, port, cancellationToken))
            {
                return;
            }

            var baseUrl = $"http://{ip}:{port}";
            using var request = new HttpRequestMessage(HttpMethod.Get, $"{baseUrl}/");
            using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

            if (response.IsSuccessStatusCode)
            {
                var body = await ReadBodySnippetAsync(response.Content, cancellationToken);
                if (LooksLikeSupportedLanCamera(body))
                {
                    results.Add(BuildCandidate(ip, port, body));
                    return;
                }
            }

            var previewCandidate = await ProbePreviewEndpointAsync(client, ip, port, "/video", cancellationToken) ??
                                   await ProbePreviewEndpointAsync(client, ip, port, "/videofeed", cancellationToken);

            if (previewCandidate is not null)
            {
                results.Add(previewCandidate);
            }
        }
        catch
        {
            // Ignore hosts that do not respond during LAN discovery.
        }
        finally
        {
            semaphore.Release();
        }
    }
}

public sealed class IpWebcamCandidate
{
    public string Name { get; set; } = string.Empty;
    public string IpAddress { get; set; } = string.Empty;
    public int Port { get; set; }
    public string BaseUrl { get; set; } = string.Empty;
    public string PreviewUrl { get; set; } = string.Empty;
    public string SnapshotUrl { get; set; } = string.Empty;
    public IReadOnlyList<string> RtspUrls { get; set; } = Array.Empty<string>();
}

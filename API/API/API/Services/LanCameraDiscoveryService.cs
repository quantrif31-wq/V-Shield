using System.Collections.Concurrent;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
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
        if (_cache.TryGetValue(cacheKey, out IReadOnlyList<IpWebcamCandidate>? cached) && cached is not null)
        {
            return cached;
        }

        var localIps = GetPrivateLocalIps();
        var subnetPrefixes = localIps
            .Select(ToSubnetPrefix)
            .Where(prefix => !string.IsNullOrWhiteSpace(prefix))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToArray();

        if (subnetPrefixes.Length == 0)
        {
            return Array.Empty<IpWebcamCandidate>();
        }

        var client = _httpClientFactory.CreateClient();
        client.Timeout = TimeSpan.FromMilliseconds(1200);

        var results = new ConcurrentBag<IpWebcamCandidate>();
        using var semaphore = new SemaphoreSlim(48);
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

        _cache.Set(cacheKey, cameras, TimeSpan.FromSeconds(20));
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

            foreach (var address in networkInterface.GetIPProperties().UnicastAddresses)
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

    private static string BuildDisplayName(string ip, string? title)
    {
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

        Add("h264.sdp");
        Add("h264_ulaw.sdp");
        Add("h264_pcm.sdp");

        return candidates;
    }

    private static IpWebcamCandidate BuildCandidate(string ip, int port, string body)
    {
        var baseUrl = $"http://{ip}:{port}";
        return new IpWebcamCandidate
        {
            Name = BuildDisplayName(ip, ExtractTitle(body)),
            IpAddress = ip,
            Port = port,
            BaseUrl = baseUrl,
            PreviewUrl = $"{baseUrl}/videofeed",
            SnapshotUrl = $"{baseUrl}/shot.jpg",
            RtspUrls = BuildRtspUrls(ip, port, body)
        };
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
            var baseUrl = $"http://{ip}:{port}";
            using var request = new HttpRequestMessage(HttpMethod.Get, $"{baseUrl}/");
            using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                return;
            }

            var body = await response.Content.ReadAsStringAsync(cancellationToken);
            if (!LooksLikeIpWebcam(body))
            {
                return;
            }

            results.Add(BuildCandidate(ip, port, body));
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

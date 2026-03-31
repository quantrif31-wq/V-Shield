using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using API.Data;
using API.Models;
using API.DTOs;
using System.Diagnostics;
using System.Text;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class SetCamController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly IConfiguration _configuration;

        public SetCamController(ApplicationDbContext context, IConfiguration configuration)
        {
            _context = context;
            _configuration = configuration;
        }

        // ================= GET ALL =================
        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var cams = await _context.Cameras
                .Include(c => c.Gate)
                .Select(c => new CameraDTO
                {
                    CameraId = c.CameraId,
                    CameraName = c.CameraName,
                    CameraType = c.CameraType,
                    GateId = c.GateId,
                    StreamUrl = c.StreamUrl,
                    UrlView = c.UrlView,
                    GateName = c.Gate != null ? c.Gate.GateName : null
                })
                .ToListAsync();

            return Ok(cams);
        }

        // ================= GET BY ID =================
        [HttpGet("{id}")]
        public async Task<IActionResult> GetById(int id)
        {
            var cam = await _context.Cameras
                .Include(c => c.Gate)
                .Where(c => c.CameraId == id)
                .Select(c => new CameraDTO
                {
                    CameraId = c.CameraId,
                    CameraName = c.CameraName,
                    CameraType = c.CameraType,
                    GateId = c.GateId,
                    StreamUrl = c.StreamUrl,
                    UrlView = c.UrlView,
                    GateName = c.Gate != null ? c.Gate.GateName : null
                })
                .FirstOrDefaultAsync();

            if (cam == null)
                return NotFound("Không tìm thấy camera");

            return Ok(cam);
        }

        // ================= CREATE =================
        [HttpPost]
        public async Task<IActionResult> Create([FromBody] SetCamRequest request)
        {
            if (request == null)
                return BadRequest(new { message = "Dữ liệu camera không hợp lệ" });

            var cameraName = request.CameraName?.Trim();
            var cameraType = request.CameraType?.Trim();
            var streamUrl = request.StreamUrl?.Trim();

            if (string.IsNullOrWhiteSpace(cameraName))
                return BadRequest(new { message = "Tên camera không được rỗng" });

            if (request.GateId.HasValue)
            {
                var gateExists = await _context.Gates.AnyAsync(g => g.GateId == request.GateId.Value);
                if (!gateExists)
                {
                    return BadRequest(new { message = "Gate ID không tồn tại" });
                }
            }

            var camera = new Camera
            {
                CameraName = cameraName,
                GateId = request.GateId,
                CameraType = string.IsNullOrWhiteSpace(cameraType) ? null : cameraType,
                StreamUrl = string.IsNullOrWhiteSpace(streamUrl) ? null : streamUrl
            };

            _context.Cameras.Add(camera);
            await _context.SaveChangesAsync();

            camera.UrlView = BuildCameraViewUrl(camera.StreamUrl, camera.CameraId);
            await _context.SaveChangesAsync();

            return Ok(camera);
        }

        // ================= UPDATE =================
        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, [FromBody] SetCamRequest request)
        {
            var cam = await _context.Cameras.FindAsync(id);

            if (cam == null)
                return NotFound("Camera không tồn tại");

            var cameraName = request.CameraName?.Trim();
            var cameraType = request.CameraType?.Trim();
            var streamUrl = request.StreamUrl?.Trim();

            if (string.IsNullOrWhiteSpace(cameraName))
                return BadRequest(new { message = "Tên camera không được rỗng" });

            if (request.GateId.HasValue)
            {
                var gateExists = await _context.Gates.AnyAsync(g => g.GateId == request.GateId.Value);
                if (!gateExists)
                {
                    return BadRequest(new { message = "Gate ID không tồn tại" });
                }
            }

            cam.CameraName = cameraName;
            cam.CameraType = string.IsNullOrWhiteSpace(cameraType) ? null : cameraType;
            cam.GateId = request.GateId;
            cam.StreamUrl = string.IsNullOrWhiteSpace(streamUrl) ? null : streamUrl;
            cam.UrlView = BuildCameraViewUrl(cam.StreamUrl, cam.CameraId);

            await _context.SaveChangesAsync();

            return Ok(cam);
        }

        // ================= DELETE =================
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(int id)
        {
            var cam = await _context.Cameras.FindAsync(id);

            if (cam == null)
                return NotFound("Không tồn tại");

            _context.Cameras.Remove(cam);
            await _context.SaveChangesAsync();

            return Ok();
        }

        // ================= 🔥 RELOAD GO2RTC =================
        [HttpPost("reload-go2rtc")]
        public async Task<IActionResult> ReloadGo2Rtc()
        {
            try
            {
                // ===== LẤY CAMERA CÓ StreamUrl =====
                var cameras = await _context.Cameras
                    .Where(c => !string.IsNullOrEmpty(c.StreamUrl))
                    .ToListAsync();

                if (!cameras.Any())
                    return BadRequest("Không có camera nào có StreamUrl");

                // ===== BUILD YAML =====
                var yaml = new StringBuilder();
                yaml.AppendLine("streams:");

                foreach (var cam in cameras)
                {
                    var normalizedStreamUrl = NormalizeCameraUrl(cam.StreamUrl);
                    cam.UrlView = BuildCameraViewUrl(normalizedStreamUrl, cam.CameraId);

                    if (!ShouldProxyViaGo2Rtc(normalizedStreamUrl))
                    {
                        continue;
                    }

                    // 👉 dùng CameraId để không bị lệch cam
                    var streamName = $"cam{cam.CameraId}";

                    yaml.AppendLine($"  {streamName}:");
                    yaml.AppendLine($"    - {normalizedStreamUrl}");
                }

                yaml.AppendLine();
                yaml.AppendLine("webrtc:");
                yaml.AppendLine("  listen: \":8555\"");
                yaml.AppendLine("  candidates:");
                yaml.AppendLine("    - 127.0.0.1:8555");
                yaml.AppendLine("api:\r\n  origin: \"*\"");

                // ===== PATH =====
                var basePath = Directory.GetCurrentDirectory();

                var go2rtcPath = Path.GetFullPath(
                    Path.Combine(basePath, "..", "..", "..", "AI_Project", "cam", "go2rtc_win64")
                );

                var yamlPath = Path.Combine(go2rtcPath, "go2rtc.yaml");
                var exePath = Path.Combine(go2rtcPath, "go2rtc.exe");

                // ===== GHI FILE YAML =====
                await System.IO.File.WriteAllTextAsync(yamlPath, yaml.ToString());

                // ===== LƯU DB (QUAN TRỌNG) =====
                await _context.SaveChangesAsync();

                // ===== STOP PROCESS CŨ =====
                foreach (var proc in Process.GetProcessesByName("go2rtc"))
                {
                    proc.Kill();
                }

                // ===== START LẠI =====
                Process.Start(new ProcessStartInfo
                {
                    FileName = exePath,
                    WorkingDirectory = go2rtcPath,
                    UseShellExecute = true
                });

                return Ok(new
                {
                    message = "Reload go2rtc thành công",
                    yaml = yaml.ToString()
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine("🔥 ERROR: " + ex.ToString());

                return StatusCode(500, new
                {
                    message = ex.Message,
                    detail = ex.InnerException?.Message,
                    stack = ex.StackTrace
                });
            }
        }

        // ================= STOP =================
        [HttpPost("stop-go2rtc")]
        public IActionResult StopGo2Rtc()
        {
            try
            {
                var processes = Process.GetProcessesByName("go2rtc");

                foreach (var proc in processes)
                {
                    proc.Kill();
                }

                return Ok("Đã tắt go2rtc");
            }
            catch (Exception ex)
            {
                return StatusCode(500, ex.Message);
            }
        }

        private static string? NormalizeCameraUrl(string? value)
        {
            var normalized = value?.Trim();
            return string.IsNullOrWhiteSpace(normalized) ? null : normalized;
        }

        private static bool IsDirectWebStream(string? streamUrl)
        {
            if (string.IsNullOrWhiteSpace(streamUrl))
            {
                return false;
            }

            if (streamUrl.StartsWith("/", StringComparison.Ordinal))
            {
                return true;
            }

            return Uri.TryCreate(streamUrl, UriKind.Absolute, out var uri) &&
                   (uri.Scheme == Uri.UriSchemeHttp || uri.Scheme == Uri.UriSchemeHttps);
        }

        private static bool ShouldProxyViaGo2Rtc(string? streamUrl) =>
            !string.IsNullOrWhiteSpace(streamUrl) && !IsDirectWebStream(streamUrl);

        private string? BuildCameraViewUrl(string? streamUrl, int cameraId)
        {
            var normalizedStreamUrl = NormalizeCameraUrl(streamUrl);
            if (string.IsNullOrWhiteSpace(normalizedStreamUrl))
            {
                return null;
            }

            if (IsDirectWebStream(normalizedStreamUrl))
            {
                return BuildDirectWebStreamUrl(normalizedStreamUrl);
            }

            var go2RtcPublicBaseUrl = ResolveGo2RtcPublicBaseUrl();
            return $"{go2RtcPublicBaseUrl}/stream.html?src=cam{cameraId}";
        }

        private string BuildDirectWebStreamUrl(string streamUrl)
        {
            if (!streamUrl.StartsWith("/", StringComparison.Ordinal))
            {
                return streamUrl;
            }

            return $"{ResolvePublicAppBaseUrl()}{streamUrl}";
        }

        private string ResolveGo2RtcPublicBaseUrl()
        {
            var configuredGo2RtcBaseUrl = _configuration["AppSettings:Go2RtcPublicBaseUrl"];
            if (!string.IsNullOrWhiteSpace(configuredGo2RtcBaseUrl))
            {
                return NormalizeBaseUrl(configuredGo2RtcBaseUrl);
            }

            return $"{ResolvePublicAppBaseUrl()}/go2rtc";
        }

        private string ResolvePublicAppBaseUrl()
        {
            var configuredFrontendUrl = _configuration["AppSettings:FrontendUrl"];
            if (!string.IsNullOrWhiteSpace(configuredFrontendUrl))
            {
                return NormalizeBaseUrl(configuredFrontendUrl);
            }

            return NormalizeBaseUrl($"{Request.Scheme}://{Request.Host}");
        }

        private static string NormalizeBaseUrl(string value) =>
            value.Trim().TrimEnd('/');
    }
}

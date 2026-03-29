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

        public SetCamController(ApplicationDbContext context)
        {
            _context = context;
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
        public async Task<IActionResult> Create(Camera camera)
        {
            if (string.IsNullOrEmpty(camera.CameraName))
                return BadRequest("Tên camera không được rỗng");

            _context.Cameras.Add(camera);
            await _context.SaveChangesAsync();

            return Ok(camera);
        }

        // ================= UPDATE =================
        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, Camera updated)
        {
            var cam = await _context.Cameras.FindAsync(id);

            if (cam == null)
                return NotFound("Camera không tồn tại");

            cam.CameraName = updated.CameraName;
            cam.CameraType = updated.CameraType;
            cam.GateId = updated.GateId;
            cam.StreamUrl = updated.StreamUrl;

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

                // lấy domain động
                var host = $"{Request.Scheme}://{Request.Host}";

                foreach (var cam in cameras)
                {
                    // 👉 dùng CameraId để không bị lệch cam
                    var streamName = $"cam{cam.CameraId}";

                    yaml.AppendLine($"  {streamName}:");
                    yaml.AppendLine($"    - {cam.StreamUrl}");

                    // 👉 AUTO UPDATE UrlView
                    cam.UrlView = $"http://localhost:1984/stream.html?src={streamName}";
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
    }
}
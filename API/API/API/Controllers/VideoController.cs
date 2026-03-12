using System.Security.Claims;
using API.Data;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    [Authorize] // ⭐ dùng cơ chế chung
    public class VideoController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly IWebHostEnvironment _env;

        public VideoController(ApplicationDbContext context, IWebHostEnvironment env)
        {
            _context = context;
            _env = env;
        }

        [HttpPost("upload")]
        [Consumes("multipart/form-data")]
        [RequestSizeLimit(50_000_000)]
        public async Task<IActionResult> UploadVideo([FromForm] UploadVideoRequest request)
        {
            var file = request.File;
            var employeeId = request.EmployeeId;

            if (file == null || file.Length == 0)
                return BadRequest(new { message = "Không có file" });

            if (file.Length > 50 * 1024 * 1024)
                return BadRequest(new { message = "Video quá lớn" });

            var ext = Path.GetExtension(file.FileName).ToLower();
            var allowed = new[] { ".mp4", ".mov", ".avi" };

            if (!allowed.Contains(ext))
                return BadRequest(new { message = "Sai định dạng video" });

            var userIdClaim = User.FindFirstValue(ClaimTypes.NameIdentifier);

            if (userIdClaim == null)
                return Unauthorized();

            int userId = int.Parse(userIdClaim);

            var user = await _context.AppUsers
                .Include(u => u.Employee)
                .FirstOrDefaultAsync(u => u.UserId == userId);

            if (user == null)
                return Unauthorized();

            int finalEmployeeId;

            if (user.Role == "Admin")
            {
                if (employeeId == null)
                    return BadRequest(new { message = "Admin phải chọn nhân viên" });

                finalEmployeeId = employeeId.Value;
            }
            else
            {
                if (user.Employee == null)
                    return BadRequest(new { message = "User chưa liên kết với nhân viên" });

                finalEmployeeId = user.Employee.EmployeeId;
            }

            string folder = Path.Combine(
                _env.WebRootPath,
                "uploads",
                "VideoFace"
            );

            if (!Directory.Exists(folder))
                Directory.CreateDirectory(folder);

            string fileName =
                $"emp_{finalEmployeeId}_{DateTime.Now:yyyyMMddHHmmss}{ext}";

            string path = Path.Combine(folder, fileName);

            using (var stream = new FileStream(path, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }

            var video = new EmployeeFaceVideo
            {
                EmployeeId = finalEmployeeId,
                FileName = fileName,
                FilePath = "/uploads/VideoFace/" + fileName,
                FileSize = file.Length,
                CreatedAt = DateTime.Now
            };

            _context.EmployeeFaceVideos.Add(video);

            await _context.SaveChangesAsync();

            return Ok(new
            {
                message = "Upload thành công",
                video.FilePath
            });
        }

        // ⭐ Lấy video theo nhân viên
        [HttpGet("employee/{employeeId}")]
        public async Task<IActionResult> GetVideosByEmployee(int employeeId)
        {
            var videos = await _context.EmployeeFaceVideos
                .Where(v => v.EmployeeId == employeeId)
                .OrderByDescending(v => v.CreatedAt)
                .ToListAsync();

            return Ok(videos);
        }

        // ⭐ chỉ admin được xóa
        [Authorize(Roles = "Admin")]
        [HttpDelete("{id}")]
        public async Task<IActionResult> DeleteVideo(int id)
        {
            var video = await _context.EmployeeFaceVideos.FindAsync(id);

            if (video == null)
                return NotFound();

            var path = Path.Combine(_env.WebRootPath, video.FilePath.TrimStart('/'));

            if (System.IO.File.Exists(path))
                System.IO.File.Delete(path);

            _context.EmployeeFaceVideos.Remove(video);

            await _context.SaveChangesAsync();

            return Ok();
        }
    }
}
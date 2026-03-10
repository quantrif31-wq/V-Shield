using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using API.Models;
using API.Data;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class BienSoController : ControllerBase
    {
        private readonly ApplicationDbContext _context;

        public BienSoController(ApplicationDbContext context)
        {
            _context = context;
        }

        // =========================
        // LẤY DANH SÁCH CAMERA
        // =========================

        [HttpGet("cameras")]
        public async Task<IActionResult> GetCameras()
        {
            var cameras = await _context.CameraPlates
                .Select(x => new
                {
                    CameraIP = x.CameraIP
                })
                .ToListAsync();

            return Ok(cameras);
        }

        // =========================
        // LẤY TẤT CẢ BIỂN SỐ REALTIME
        // =========================

        [HttpGet("plates")]
        public async Task<IActionResult> GetPlates()
        {
            var plates = await _context.CameraPlates
                .OrderByDescending(x => x.LastUpdate)
                .Select(p => new
                {
                    p.CameraIP,
                    p.PlateNumber,
                    p.X1,
                    p.Y1,
                    p.X2,
                    p.Y2,
                    p.LastUpdate
                })
                .ToListAsync();

            return Ok(plates);
        }

        // =========================
        // LẤY BIỂN SỐ THEO CAMERA
        // =========================

        [HttpGet("plate")]
        public async Task<IActionResult> GetPlate(string ip)
        {
            var plate = await _context.CameraPlates
                .FirstOrDefaultAsync(x => x.CameraIP == ip);

            if (plate == null)
                return NotFound();

            return Ok(plate);
        }

        // =========================
        // CAMERA + PLATE (dashboard)
        // =========================

        [HttpGet("camera-plates")]
        public async Task<IActionResult> GetCameraPlates()
        {
            var data = await _context.Cameras
                .Select(c => new
                {
                    c.CameraId,
                    c.CameraName,
                    c.CameraType,

                    Plate = _context.CameraPlates
                        .Where(p => p.CameraIP == c.CameraName)
                        .Select(p => new
                        {
                            p.PlateNumber,
                            p.X1,
                            p.Y1,
                            p.X2,
                            p.Y2,
                            p.LastUpdate
                        })
                        .FirstOrDefault()
                })
                .ToListAsync();

            return Ok(data);
        }
    }
}
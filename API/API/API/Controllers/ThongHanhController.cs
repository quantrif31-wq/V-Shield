using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Net.Http;
using System.Threading.Tasks;
using API.Data;
using API.Models;
using Newtonsoft.Json.Linq;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class GateController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly HttpClient _client;

        string faceApi = "http://127.0.0.1:8000";

        public GateController(ApplicationDbContext context)
        {
            _context = context;
            _client = new HttpClient();
        }

        // ======================================
        // API DUY NHẤT
        // ======================================

        [HttpGet("scan")]
        public async Task<IActionResult> Scan()
        {
            try
            {
                // =========================
                // 1. Lấy dữ liệu FaceAI
                // =========================

                var res = await _client.GetAsync($"{faceApi}/camera/status");

                if (!res.IsSuccessStatusCode)
                    return BadRequest("Face AI not running");

                var json = await res.Content.ReadAsStringAsync();

                var data = JObject.Parse(json);

                bool confirmed = data["session_confirmed"]?.Value<bool>() ?? false;

                if (!confirmed)
                {
                    return Ok(new
                    {
                        status = "WAIT_FACE"
                    });
                }

                int employeeId = int.Parse(data["employee_id"]?.ToString() ?? "0");

                if (employeeId == 0)
                {
                    return Ok(new
                    {
                        status = "NO_EMPLOYEE"
                    });
                }

                // =========================
                // 2. Lấy biển hiện tại
                // =========================

                var plate = await _context.CameraPlates
                    .OrderByDescending(x => x.LastUpdate)
                    .FirstOrDefaultAsync();

                if (plate == null || string.IsNullOrEmpty(plate.PlateNumber))
                {
                    return Ok(new
                    {
                        status = "WAIT_PLATE"
                    });
                }

                string plateNumber = plate.PlateNumber.Trim();

                // =========================
                // 3. Kiểm tra xe
                // =========================

                var vehicle = await _context.Vehicles
                    .FirstOrDefaultAsync(x =>
                        x.EmployeeId == employeeId &&
                        x.LicensePlate == plateNumber);

                string action;

                if (vehicle == null)
                {
                    vehicle = new Vehicle
                    {
                        EmployeeId = employeeId,
                        LicensePlate = plateNumber,
                        ParkingStatus = "IN"
                    };

                    _context.Vehicles.Add(vehicle);

                    action = "REGISTER_AND_IN";
                }
                else
                {
                    if (vehicle.ParkingStatus == "IN")
                    {
                        vehicle.ParkingStatus = "OUT";
                        action = "VEHICLE_OUT";
                    }
                    else
                    {
                        vehicle.ParkingStatus = "IN";
                        action = "VEHICLE_IN";
                    }
                }

                await _context.SaveChangesAsync();

                // =========================
                // 4. Ghi log
                // =========================

                var log = new AccessLog
                {
                    EmployeeId = employeeId,
                    CapturedLicensePlate = plateNumber,
                    Direction = vehicle.ParkingStatus,
                    ResultStatus = "SUCCESS",
                    Timestamp = DateTime.Now
                };

                _context.AccessLogs.Add(log);

                await _context.SaveChangesAsync();

                // =========================
                // 5. trả kết quả
                // =========================

                return Ok(new
                {
                    status = "SUCCESS",
                    employeeId = employeeId,
                    plate = plateNumber,
                    action = action,
                    parkingStatus = vehicle.ParkingStatus
                });
            }
            catch (Exception ex)
            {
                return BadRequest(ex.Message);
            }
        }
    }
}
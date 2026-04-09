using API.Data;
using API.Models;
using API.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace API.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class GateController : ControllerBase
    {
        private readonly ApplicationDbContext _context;
        private readonly GateSyncOptions _gateSyncOptions;

        public GateController(ApplicationDbContext context, IOptions<GateSyncOptions> gateSyncOptions)
        {
            _context = context;
            _gateSyncOptions = gateSyncOptions.Value;
        }

        /// <summary>
        /// Nhận biển số + employeeId.
        /// - Nếu đúng biển số + đúng employee đã tồn tại => toggle IN/OUT.
        /// - Nếu chưa có đúng cặp đó:
        ///     + Nếu biển đang thuộc người khác và đang IN => fail.
        ///     + Ngược lại => thêm mới với trạng thái IN.
        /// </summary>
        [HttpPost("scan")]
        public async Task<IActionResult> ScanVehicle([FromBody] GateScanRequest request)
        {
            if (request == null)
            {
                return BadRequest(GateApiResponse.CreateError("Dữ liệu gửi lên không hợp lệ."));
            }

            var normalizedPlate = NormalizeLicensePlate(request.LicensePlate);

            if (string.IsNullOrWhiteSpace(normalizedPlate))
            {
                return BadRequest(GateApiResponse.CreateError("Biển số không được để trống."));
            }

            if (request.EmployeeId <= 0)
            {
                return BadRequest(GateApiResponse.CreateError("EmployeeId không hợp lệ."));
            }

            var employee = await _context.Employees
                .FirstOrDefaultAsync(e => e.EmployeeId == request.EmployeeId);

            if (employee == null)
            {
                return NotFound(GateApiResponse.CreateError($"Không tìm thấy nhân viên có id = {request.EmployeeId}."));
            }

            await using var transaction = await _context.Database.BeginTransactionAsync();

            try
            {
                var samePlateVehicles = await _context.Vehicles
                    .Where(v => v.LicensePlate != null)
                    .ToListAsync();

                samePlateVehicles = samePlateVehicles
                    .Where(v => NormalizeLicensePlate(v.LicensePlate) == normalizedPlate)
                    .ToList();

                var currentVehicle = samePlateVehicles
                    .FirstOrDefault(v => v.EmployeeId == request.EmployeeId);

                if (currentVehicle != null)
                {
                    var oldStatus = NormalizeParkingStatus(currentVehicle.ParkingStatus);
                    var newStatus = oldStatus == "IN" ? "OUT" : "IN";

                    currentVehicle.ParkingStatus = newStatus;

                    _context.AccessLogs.Add(new AccessLog
                    {
                        Timestamp = DateTime.Now,
                        Direction = newStatus,
                        GateId = request.GateId,
                        CameraId = request.CameraId,
                        CapturedLicensePlate = currentVehicle.LicensePlate,
                        EmployeeId = request.EmployeeId,
                        ResultStatus = "SUCCESS",
                        IsBypass = false,
                        Note = $"Đổi trạng thái xe từ {oldStatus} sang {newStatus}"
                    });

                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();

                    return Ok(GateApiResponse.CreateSuccess(
                        $"Cập nhật trạng thái thành công: {oldStatus} -> {newStatus}.",
                        new
                        {
                            currentVehicle.VehicleId,
                            currentVehicle.LicensePlate,
                            currentVehicle.EmployeeId,
                            currentVehicle.VehicleTypeId,
                            currentVehicle.Description,
                            currentVehicle.ParkingStatus
                        }));
                }

                // 2. Nếu chưa có đúng cặp đó, kiểm tra biển có đang thuộc người khác và đang IN không
                var conflictVehicle = samePlateVehicles.FirstOrDefault(v =>
                    v.EmployeeId != request.EmployeeId &&
                    NormalizeParkingStatus(v.ParkingStatus) == "IN");

                if (conflictVehicle != null)
                {
                    _context.AccessLogs.Add(new AccessLog
                    {
                        Timestamp = DateTime.Now,
                        Direction = "IN",
                        GateId = request.GateId,
                        CameraId = request.CameraId,
                        CapturedLicensePlate = request.LicensePlate,
                        EmployeeId = request.EmployeeId,
                        ResultStatus = "FAILED",
                        IsBypass = false,
                        Note = $"Biển số đang được gửi bởi nhân viên có id là {conflictVehicle.EmployeeId}"
                    });

                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();

                    return Conflict(GateApiResponse.CreateError(
                        $"Biển số đang được gửi bởi 1 nhân viên có id là {conflictVehicle.EmployeeId}."));
                }

                var newVehicle = new Vehicle
                {
                    LicensePlate = normalizedPlate,
                    EmployeeId = request.EmployeeId,
                    VehicleTypeId = request.VehicleTypeId,
                    Description = request.Description,
                    ParkingStatus = "IN"
                };

                _context.Vehicles.Add(newVehicle);

                _context.AccessLogs.Add(new AccessLog
                {
                    Timestamp = DateTime.Now,
                    Direction = "IN",
                    GateId = request.GateId,
                    CameraId = request.CameraId,
                    CapturedLicensePlate = normalizedPlate,
                    EmployeeId = request.EmployeeId,
                    ResultStatus = "SUCCESS",
                    IsBypass = false,
                    Note = "Thêm mới phương tiện và cho vào bãi với trạng thái IN"
                });

                await _context.SaveChangesAsync();
                await transaction.CommitAsync();

                return Ok(GateApiResponse.CreateSuccess(
                    "Chưa có dữ liệu trước đó. Đã thêm mới phương tiện với trạng thái IN.",
                    new
                    {
                        newVehicle.VehicleId,
                        newVehicle.LicensePlate,
                        newVehicle.EmployeeId,
                        newVehicle.VehicleTypeId,
                        newVehicle.Description,
                        newVehicle.ParkingStatus
                    }));
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();

                return StatusCode(500, GateApiResponse.CreateError(
                    "Có lỗi xảy ra khi xử lý dữ liệu.",
                    ex.Message));
            }
        }

        [HttpPost("local-confirm")]
        public async Task<IActionResult> ConfirmVehicleLocally([FromBody] GateScanRequest request)
        {
            if (request == null)
            {
                return BadRequest(GateApiResponse.CreateError("Dữ liệu gửi lên không hợp lệ."));
            }

            var normalizedPlate = NormalizeLicensePlate(request.LicensePlate);

            if (string.IsNullOrWhiteSpace(normalizedPlate))
            {
                return BadRequest(GateApiResponse.CreateError("Biển số không được để trống."));
            }

            if (request.EmployeeId <= 0)
            {
                return BadRequest(GateApiResponse.CreateError("EmployeeId không hợp lệ."));
            }

            var employee = await _context.Employees
                .FirstOrDefaultAsync(e => e.EmployeeId == request.EmployeeId);

            if (employee == null)
            {
                return NotFound(GateApiResponse.CreateError($"Không tìm thấy nhân viên có id = {request.EmployeeId}."));
            }

            var syncDelayMinutes = Math.Max(1, _gateSyncOptions.SyncDelayMinutes);
            var nowUtc = DateTime.UtcNow;

            await using var transaction = await _context.Database.BeginTransactionAsync();

            try
            {
                var accessLog = new AccessLog
                {
                    Timestamp = DateTime.Now,
                    Direction = "PENDING",
                    GateId = request.GateId,
                    CameraId = request.CameraId,
                    CapturedLicensePlate = normalizedPlate,
                    EmployeeId = request.EmployeeId,
                    ResultStatus = "PENDING_SYNC",
                    IsBypass = false,
                    Note = $"Xác nhận local thành công. Chờ đồng bộ VPS sau {syncDelayMinutes} phút."
                };

                _context.AccessLogs.Add(accessLog);
                await _context.SaveChangesAsync();

                var pendingGateSync = new PendingGateSync
                {
                    AccessLogId = accessLog.LogId,
                    EmployeeId = request.EmployeeId,
                    LicensePlate = normalizedPlate,
                    VehicleTypeId = request.VehicleTypeId,
                    Description = request.Description?.Trim(),
                    GateId = request.GateId,
                    CameraId = request.CameraId,
                    Status = "PENDING",
                    CreatedAt = nowUtc,
                    SyncDueAt = nowUtc.AddMinutes(syncDelayMinutes),
                    RetryCount = 0
                };

                _context.PendingGateSyncs.Add(pendingGateSync);
                await _context.SaveChangesAsync();
                await transaction.CommitAsync();

                return Ok(GateApiResponse.CreateSuccess(
                    $"Đã xác nhận tại local. Hệ thống sẽ đồng bộ VPS sau {syncDelayMinutes} phút.",
                    new
                    {
                        accessLog.LogId,
                        pendingGateSync.PendingGateSyncId,
                        pendingGateSync.SyncDueAt,
                        EmployeeId = request.EmployeeId,
                        LicensePlate = normalizedPlate,
                        request.GateId,
                        request.CameraId
                    }));
            }
            catch (Exception ex)
            {
                await transaction.RollbackAsync();

                return StatusCode(500, GateApiResponse.CreateError(
                    "Có lỗi xảy ra khi xác nhận local.",
                    ex.Message));
            }
        }

        [HttpGet("vehicle-by-employee/{employeeId:int}")]
        public async Task<IActionResult> GetVehiclesByEmployee(int employeeId)
        {
            var employeeExists = await _context.Employees
                .AnyAsync(e => e.EmployeeId == employeeId);

            if (!employeeExists)
            {
                return NotFound(GateApiResponse.CreateError($"Không tìm thấy nhân viên có id = {employeeId}."));
            }

            var vehicles = await _context.Vehicles
                .Where(v => v.EmployeeId == employeeId)
                .Select(v => new
                {
                    v.VehicleId,
                    v.LicensePlate,
                    v.VehicleTypeId,
                    v.EmployeeId,
                    v.Description,
                    v.ParkingStatus
                })
                .ToListAsync();

            return Ok(GateApiResponse.CreateSuccess("Lấy danh sách xe thành công.", vehicles));
        }

        [HttpGet("vehicle-by-plate/{licensePlate}")]
        public async Task<IActionResult> GetVehicleByPlate(string licensePlate)
        {
            var normalizedPlate = NormalizeLicensePlate(licensePlate);

            if (string.IsNullOrWhiteSpace(normalizedPlate))
            {
                return BadRequest(GateApiResponse.CreateError("Biển số không hợp lệ."));
            }

            var vehicles = await _context.Vehicles
                .Where(v => v.LicensePlate != null)
                .ToListAsync();

            var result = vehicles
                .Where(v => NormalizeLicensePlate(v.LicensePlate) == normalizedPlate)
                .Select(v => new
                {
                    v.VehicleId,
                    v.LicensePlate,
                    v.VehicleTypeId,
                    v.EmployeeId,
                    v.Description,
                    v.ParkingStatus
                })
                .ToList();

            if (!result.Any())
            {
                return NotFound(GateApiResponse.CreateError("Không tìm thấy biển số này."));
            }

            return Ok(GateApiResponse.CreateSuccess("Lấy thông tin xe thành công.", result));
        }

        [HttpGet("logs-by-plate/{licensePlate}")]
        public async Task<IActionResult> GetLogsByPlate(string licensePlate)
        {
            var normalizedPlate = NormalizeLicensePlate(licensePlate);

            if (string.IsNullOrWhiteSpace(normalizedPlate))
            {
                return BadRequest(GateApiResponse.CreateError("Biển số không hợp lệ."));
            }

            var logs = await _context.AccessLogs
                .Where(x => x.CapturedLicensePlate != null)
                .OrderByDescending(x => x.Timestamp)
                .ToListAsync();

            var result = logs
                .Where(x => NormalizeLicensePlate(x.CapturedLicensePlate) == normalizedPlate)
                .Select(x => new
                {
                    x.LogId,
                    x.Timestamp,
                    x.Direction,
                    x.GateId,
                    x.CameraId,
                    x.CapturedLicensePlate,
                    x.EmployeeId,
                    x.ResultStatus,
                    x.IsBypass,
                    x.Note
                })
                .ToList();

            return Ok(GateApiResponse.CreateSuccess("Lấy lịch sử theo biển số thành công.", result));
        }

        [HttpGet("logs-by-employee/{employeeId:int}")]
        public async Task<IActionResult> GetLogsByEmployee(int employeeId)
        {
            var employeeExists = await _context.Employees
                .AnyAsync(e => e.EmployeeId == employeeId);

            if (!employeeExists)
            {
                return NotFound(GateApiResponse.CreateError($"Không tìm thấy nhân viên có id = {employeeId}."));
            }

            var result = await _context.AccessLogs
                .Where(x => x.EmployeeId == employeeId)
                .OrderByDescending(x => x.Timestamp)
                .Select(x => new
                {
                    x.LogId,
                    x.Timestamp,
                    x.Direction,
                    x.GateId,
                    x.CameraId,
                    x.CapturedLicensePlate,
                    x.EmployeeId,
                    x.ResultStatus,
                    x.IsBypass,
                    x.Note
                })
                .ToListAsync();

            return Ok(GateApiResponse.CreateSuccess("Lấy lịch sử theo nhân viên thành công.", result));
        }

        private static string NormalizeLicensePlate(string? plate)
        {
            if (string.IsNullOrWhiteSpace(plate))
            {
                return string.Empty;
            }

            return plate.Trim()
                .ToUpper()
                .Replace(" ", string.Empty)
                .Replace("-", string.Empty);
        }

        private static string NormalizeParkingStatus(string? status)
        {
            if (string.IsNullOrWhiteSpace(status))
            {
                return "OUT";
            }

            return status.Trim().ToUpper() == "IN" ? "IN" : "OUT";
        }
    }

    public class GateScanRequest
    {
        public string LicensePlate { get; set; } = string.Empty;
        public int EmployeeId { get; set; }
        public int? VehicleTypeId { get; set; }
        public string? Description { get; set; }
        public int? GateId { get; set; }
        public int? CameraId { get; set; }
    }

    public class GateApiResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public object? Data { get; set; }

        public static GateApiResponse CreateSuccess(string message, object? data = null)
        {
            return new GateApiResponse
            {
                Success = true,
                Message = message,
                Data = data
            };
        }

        public static GateApiResponse CreateError(string message, object? data = null)
        {
            return new GateApiResponse
            {
                Success = false,
                Message = message,
                Data = data
            };
        }
    }
}

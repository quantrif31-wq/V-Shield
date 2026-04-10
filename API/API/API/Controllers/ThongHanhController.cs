using System.Globalization;
using System.Text;
using API.Data;
using API.Helpers;
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

        [HttpPost("scan")]
        public Task<IActionResult> ScanVehicle([FromBody] GateScanRequest request) =>
            ProcessVehicleAccessAsync(request, deferRemoteSync: false);

        [HttpPost("local-confirm")]
        public Task<IActionResult> ConfirmVehicleLocally([FromBody] GateScanRequest request) =>
            ProcessVehicleAccessAsync(request, deferRemoteSync: true);

        private async Task<IActionResult> ProcessVehicleAccessAsync(GateScanRequest request, bool deferRemoteSync)
        {
            if (request == null)
            {
                return BadRequest(GateApiResponse.CreateError("Dữ liệu gửi lên không hợp lệ."));
            }

            var plateInfo = LicensePlateHelper.Analyze(request.LicensePlate);
            var lookupPlate = plateInfo.LookupKey;
            var displayPlate = plateInfo.IsValid
                ? plateInfo.DisplayPlate
                : string.IsNullOrWhiteSpace(request.LicensePlate)
                    ? string.Empty
                    : request.LicensePlate.Trim().ToUpperInvariant();

            if (string.IsNullOrWhiteSpace(lookupPlate))
            {
                return BadRequest(GateApiResponse.CreateError("Biển số không được để trống."));
            }

            if (request.EmployeeId <= 0)
            {
                return BadRequest(GateApiResponse.CreateError("EmployeeId không hợp lệ."));
            }

            var rawDirection = request.Direction?.Trim();
            var requestedDirection = NormalizeDirection(rawDirection);

            if (!string.IsNullOrWhiteSpace(rawDirection) && requestedDirection == null)
            {
                return BadRequest(GateApiResponse.CreateError("Direction chỉ chấp nhận IN hoặc OUT."));
            }

            var employee = await _context.Employees
                .FirstOrDefaultAsync(e => e.EmployeeId == request.EmployeeId);

            if (employee == null)
            {
                return NotFound(GateApiResponse.CreateError($"Không tìm thấy nhân viên có id = {request.EmployeeId}."));
            }

            var syncDelayMinutes = deferRemoteSync
                ? Math.Max(1, _gateSyncOptions.SyncDelayMinutes)
                : 0;
            var nowUtc = DateTime.UtcNow;
            var resolvedVehicleTypeId = request.VehicleTypeId ?? await ResolveVehicleTypeIdByPlateAsync(plateInfo);

            await using var transaction = await _context.Database.BeginTransactionAsync();

            try
            {
                var samePlateVehicles = await _context.Vehicles
                    .Where(v => v.LicensePlate != null)
                    .ToListAsync();

                samePlateVehicles = samePlateVehicles
                    .Where(v => NormalizeLicensePlate(v.LicensePlate) == lookupPlate)
                    .ToList();

                var currentVehicle = samePlateVehicles
                    .FirstOrDefault(v => v.EmployeeId == request.EmployeeId);

                if (currentVehicle != null)
                {
                    if (plateInfo.IsValid && !string.Equals(currentVehicle.LicensePlate, displayPlate, StringComparison.Ordinal))
                    {
                        currentVehicle.LicensePlate = displayPlate;
                    }

                    if (!currentVehicle.VehicleTypeId.HasValue && resolvedVehicleTypeId.HasValue)
                    {
                        currentVehicle.VehicleTypeId = resolvedVehicleTypeId;
                    }

                    var oldStatus = NormalizeParkingStatus(currentVehicle.ParkingStatus);
                    var newStatus = requestedDirection ?? (oldStatus == "IN" ? "OUT" : "IN");

                    if (oldStatus == newStatus)
                    {
                        var duplicateMessage = newStatus == "IN"
                            ? "Xe này đang ở trong bãi rồi, không thể ghi nhận thêm lượt vào."
                            : "Xe này hiện đang ở ngoài bãi, không thể ghi nhận thêm lượt ra.";

                        _context.AccessLogs.Add(CreateAccessLog(
                            request,
                            currentVehicle.LicensePlate,
                            request.EmployeeId,
                            newStatus,
                            "FAILED",
                            duplicateMessage));

                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();

                        return Conflict(GateApiResponse.CreateError(duplicateMessage));
                    }

                    currentVehicle.ParkingStatus = newStatus;

                    var accessLog = CreateAccessLog(
                        request,
                        currentVehicle.LicensePlate,
                        request.EmployeeId,
                        newStatus,
                        deferRemoteSync ? "PENDING_SYNC" : "SUCCESS",
                        deferRemoteSync
                            ? $"Xác nhận local lượt {GetDirectionLabel(newStatus)} thành công. Chờ đồng bộ VPS sau {syncDelayMinutes} phút."
                            : $"Đã ghi nhận lượt {GetDirectionLabel(newStatus)}. Trạng thái xe chuyển từ {oldStatus} sang {newStatus}.");

                    _context.AccessLogs.Add(accessLog);
                    await _context.SaveChangesAsync();

                    PendingGateSync? pendingGateSync = null;
                    if (deferRemoteSync)
                    {
                        pendingGateSync = CreatePendingGateSync(
                            accessLog.LogId,
                            request,
                            currentVehicle.LicensePlate,
                            resolvedVehicleTypeId,
                            nowUtc,
                            syncDelayMinutes);
                        _context.PendingGateSyncs.Add(pendingGateSync);
                        await _context.SaveChangesAsync();
                    }

                    await transaction.CommitAsync();

                    return Ok(GateApiResponse.CreateSuccess(
                        deferRemoteSync
                            ? $"Đã xác nhận tại local lượt {GetDirectionLabel(newStatus)}. Hệ thống sẽ đồng bộ VPS sau {syncDelayMinutes} phút."
                            : $"Ghi nhận lượt {GetDirectionLabel(newStatus)} thành công.",
                        new
                        {
                            vehicle = BuildVehicleSnapshot(currentVehicle),
                            direction = newStatus,
                            accessLogId = accessLog.LogId,
                            pendingGateSyncId = pendingGateSync?.PendingGateSyncId,
                            syncDueAt = pendingGateSync?.SyncDueAt
                        }));
                }

                if (requestedDirection != null)
                {
                    var ownedByOtherEmployee = samePlateVehicles.FirstOrDefault(v => v.EmployeeId != request.EmployeeId);
                    if (ownedByOtherEmployee != null)
                    {
                        var ownershipMessage = $"Biển số này đã được đăng ký cho nhân viên có id = {ownedByOtherEmployee.EmployeeId}.";

                        _context.AccessLogs.Add(CreateAccessLog(
                            request,
                            displayPlate,
                            request.EmployeeId,
                            requestedDirection,
                            "FAILED",
                            ownershipMessage));

                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();

                        return Conflict(GateApiResponse.CreateError(ownershipMessage));
                    }

                    if (requestedDirection == "OUT")
                    {
                        const string exitWithoutVehicleMessage = "Không thể ghi nhận lượt ra vì xe chưa có trong hệ thống hoặc chưa có lượt vào trước đó.";

                        _context.AccessLogs.Add(CreateAccessLog(
                            request,
                            displayPlate,
                            request.EmployeeId,
                            requestedDirection,
                            "FAILED",
                            exitWithoutVehicleMessage));

                        await _context.SaveChangesAsync();
                        await transaction.CommitAsync();

                        return Conflict(GateApiResponse.CreateError(exitWithoutVehicleMessage));
                    }
                }

                var conflictVehicle = samePlateVehicles.FirstOrDefault(v =>
                    v.EmployeeId != request.EmployeeId &&
                    NormalizeParkingStatus(v.ParkingStatus) == "IN");

                if (conflictVehicle != null)
                {
                    var conflictDirection = requestedDirection ?? "IN";
                    var conflictMessage = $"Biển số đang được sử dụng bởi nhân viên có id = {conflictVehicle.EmployeeId}.";

                    _context.AccessLogs.Add(CreateAccessLog(
                        request,
                        displayPlate,
                        request.EmployeeId,
                        conflictDirection,
                        "FAILED",
                        conflictMessage));

                    await _context.SaveChangesAsync();
                    await transaction.CommitAsync();

                    return Conflict(GateApiResponse.CreateError(conflictMessage));
                }

                var newVehicle = new Vehicle
                {
                    LicensePlate = displayPlate,
                    EmployeeId = request.EmployeeId,
                    VehicleTypeId = resolvedVehicleTypeId,
                    Description = request.Description?.Trim(),
                    ParkingStatus = "IN"
                };

                _context.Vehicles.Add(newVehicle);
                await _context.SaveChangesAsync();

                var newVehicleAccessLog = CreateAccessLog(
                    request,
                    newVehicle.LicensePlate,
                    request.EmployeeId,
                    "IN",
                    deferRemoteSync ? "PENDING_SYNC" : "SUCCESS",
                    deferRemoteSync
                        ? $"Thêm mới phương tiện và xác nhận local lượt vào. Chờ đồng bộ VPS sau {syncDelayMinutes} phút."
                        : "Thêm mới phương tiện và ghi nhận lượt vào.");

                _context.AccessLogs.Add(newVehicleAccessLog);
                await _context.SaveChangesAsync();

                PendingGateSync? pendingGateSyncForNewVehicle = null;
                if (deferRemoteSync)
                {
                    pendingGateSyncForNewVehicle = CreatePendingGateSync(
                        newVehicleAccessLog.LogId,
                        request,
                        newVehicle.LicensePlate,
                        resolvedVehicleTypeId,
                        nowUtc,
                        syncDelayMinutes);
                    _context.PendingGateSyncs.Add(pendingGateSyncForNewVehicle);
                    await _context.SaveChangesAsync();
                }

                await transaction.CommitAsync();

                return Ok(GateApiResponse.CreateSuccess(
                    deferRemoteSync
                        ? $"Đã xác nhận tại local lượt vào. Hệ thống sẽ đồng bộ VPS sau {syncDelayMinutes} phút."
                        : "Chưa có dữ liệu trước đó. Đã thêm mới phương tiện với trạng thái IN.",
                    new
                    {
                        vehicle = BuildVehicleSnapshot(newVehicle),
                        direction = "IN",
                        accessLogId = newVehicleAccessLog.LogId,
                        pendingGateSyncId = pendingGateSyncForNewVehicle?.PendingGateSyncId,
                        syncDueAt = pendingGateSyncForNewVehicle?.SyncDueAt
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
                    LicensePlate = LicensePlateHelper.Analyze(v.LicensePlate).DisplayPlate,
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
                    LicensePlate = LicensePlateHelper.Analyze(v.LicensePlate).DisplayPlate,
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
                    CapturedLicensePlate = LicensePlateHelper.Analyze(x.CapturedLicensePlate).DisplayPlate,
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
                    CapturedLicensePlate = LicensePlateHelper.Analyze(x.CapturedLicensePlate).DisplayPlate,
                    x.EmployeeId,
                    x.ResultStatus,
                    x.IsBypass,
                    x.Note
                })
                .ToListAsync();

            return Ok(GateApiResponse.CreateSuccess("Lấy lịch sử theo nhân viên thành công.", result));
        }

        private static string NormalizeLicensePlate(string? plate) =>
            LicensePlateHelper.NormalizeLookupKey(plate);

        private static string NormalizeParkingStatus(string? status)
        {
            if (string.IsNullOrWhiteSpace(status))
            {
                return "OUT";
            }

            return status.Trim().ToUpper() == "IN" ? "IN" : "OUT";
        }

        private static string? NormalizeDirection(string? direction)
        {
            if (string.IsNullOrWhiteSpace(direction))
            {
                return null;
            }

            return direction.Trim().ToUpper() switch
            {
                "IN" => "IN",
                "OUT" => "OUT",
                _ => null
            };
        }

        private static string GetDirectionLabel(string direction) =>
            string.Equals(direction, "OUT", StringComparison.OrdinalIgnoreCase) ? "ra" : "vào";

        private static AccessLog CreateAccessLog(
            GateScanRequest request,
            string licensePlate,
            int employeeId,
            string direction,
            string resultStatus,
            string note)
        {
            return new AccessLog
            {
                Timestamp = DateTime.Now,
                Direction = direction,
                GateId = request.GateId,
                CameraId = request.CameraId,
                CapturedLicensePlate = licensePlate,
                EmployeeId = employeeId,
                ResultStatus = resultStatus,
                IsBypass = false,
                Note = note
            };
        }

        private static object BuildVehicleSnapshot(Vehicle vehicle)
        {
            var plateInfo = LicensePlateHelper.Analyze(vehicle.LicensePlate);

            return new
            {
                vehicle.VehicleId,
                LicensePlate = plateInfo.IsValid ? plateInfo.DisplayPlate : vehicle.LicensePlate,
                vehicle.EmployeeId,
                vehicle.VehicleTypeId,
                vehicle.Description,
                vehicle.ParkingStatus
            };
        }

        private static PendingGateSync CreatePendingGateSync(
            int accessLogId,
            GateScanRequest request,
            string licensePlate,
            int? vehicleTypeId,
            DateTime nowUtc,
            int syncDelayMinutes)
        {
            return new PendingGateSync
            {
                AccessLogId = accessLogId,
                EmployeeId = request.EmployeeId,
                LicensePlate = licensePlate,
                VehicleTypeId = vehicleTypeId,
                Description = request.Description?.Trim(),
                GateId = request.GateId,
                CameraId = request.CameraId,
                Status = "PENDING",
                CreatedAt = nowUtc,
                SyncDueAt = nowUtc.AddMinutes(syncDelayMinutes),
                RetryCount = 0
            };
        }

        private async Task<int?> ResolveVehicleTypeIdByPlateAsync(LicensePlateInfo plateInfo)
        {
            if (!plateInfo.IsValid)
            {
                return null;
            }

            var aliases = plateInfo.VehicleKind switch
            {
                LicensePlateVehicleKind.Car => new[] { "o to", "xe hoi", "car" },
                LicensePlateVehicleKind.Motorcycle => new[] { "xe may", "motorcycle", "motorbike", "moto" },
                _ => Array.Empty<string>()
            };

            if (aliases.Length == 0)
            {
                return null;
            }

            var vehicleTypes = await _context.VehicleTypes
                .OrderBy(vt => vt.TypeName)
                .ToListAsync();

            var matchedType = vehicleTypes.FirstOrDefault(item =>
            {
                var normalizedName = NormalizeTypeName(item.TypeName);
                return aliases.Any(alias => normalizedName.Contains(alias, StringComparison.Ordinal));
            });

            return matchedType?.VehicleTypeId;
        }

        private static string NormalizeTypeName(string? value)
        {
            var normalized = (value ?? string.Empty).Normalize(NormalizationForm.FormD);
            var builder = new StringBuilder(normalized.Length);

            foreach (var ch in normalized)
            {
                if (CharUnicodeInfo.GetUnicodeCategory(ch) != UnicodeCategory.NonSpacingMark)
                {
                    builder.Append(char.ToLowerInvariant(ch));
                }
            }

            return builder
                .ToString()
                .Normalize(NormalizationForm.FormC)
                .Trim();
        }
    }

    public class GateScanRequest
    {
        public string LicensePlate { get; set; } = string.Empty;
        public int EmployeeId { get; set; }
        public string? Direction { get; set; }
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

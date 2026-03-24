using API.Data;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/access-logs")]
[Authorize]
public class AccessLogsController : ControllerBase
{
    private static readonly string[] SuccessfulStatuses = ["APPROVED", "SUCCESS", "GRANTED", "OK", "MATCHED"];
    private readonly ApplicationDbContext _context;

    public AccessLogsController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetLogs(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? query = null,
        [FromQuery] string? direction = null,
        [FromQuery] string? resultStatus = null,
        [FromQuery] int? gateId = null,
        [FromQuery] bool? isBypass = null,
        [FromQuery] DateTime? dateFrom = null,
        [FromQuery] DateTime? dateTo = null)
    {
        page = Math.Max(page, 1);
        pageSize = Math.Clamp(pageSize, 1, 100);

        var logsQuery = BuildLogProjectionQuery();

        if (!string.IsNullOrWhiteSpace(query))
        {
            var normalized = query.Trim();
            logsQuery = logsQuery.Where(log =>
                (log.ActorName != null && log.ActorName.Contains(normalized)) ||
                (log.CapturedLicensePlate != null && log.CapturedLicensePlate.Contains(normalized)) ||
                (log.GateName != null && log.GateName.Contains(normalized)) ||
                (log.Note != null && log.Note.Contains(normalized)));
        }

        if (!string.IsNullOrWhiteSpace(direction))
        {
            var normalizedDirection = direction.Trim().ToUpper();
            logsQuery = logsQuery.Where(log => log.Direction != null && log.Direction.ToUpper() == normalizedDirection);
        }

        if (!string.IsNullOrWhiteSpace(resultStatus))
        {
            var normalizedStatus = resultStatus.Trim().ToUpper();
            logsQuery = logsQuery.Where(log => log.ResultStatus != null && log.ResultStatus.ToUpper() == normalizedStatus);
        }

        if (gateId.HasValue)
        {
            logsQuery = logsQuery.Where(log => log.GateId == gateId.Value);
        }

        if (isBypass.HasValue)
        {
            logsQuery = logsQuery.Where(log => log.IsBypass == isBypass.Value);
        }

        if (dateFrom.HasValue)
        {
            logsQuery = logsQuery.Where(log => log.Timestamp >= dateFrom.Value);
        }

        if (dateTo.HasValue)
        {
            var dateToExclusive = dateTo.Value.Date.AddDays(1);
            logsQuery = logsQuery.Where(log => log.Timestamp < dateToExclusive);
        }

        var total = await logsQuery.CountAsync();
        var items = await logsQuery
            .OrderByDescending(log => log.Timestamp)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return Ok(new
        {
            page,
            pageSize,
            total,
            items = items.Select(MapLogItem)
        });
    }

    [HttpGet("summary")]
    public async Task<IActionResult> GetSummary()
    {
        var today = DateTime.Today;
        var tomorrow = today.AddDays(1);

        var logs = await _context.AccessLogs.AsNoTracking()
            .Where(log => log.Timestamp >= today && log.Timestamp < tomorrow)
            .Select(log => new
            {
                log.Direction,
                log.IsBypass,
                log.ExceptionReasonId,
                log.ResultStatus,
                log.CapturedFaceImageUrl,
                log.CapturedLicensePlate
            })
            .ToListAsync();

        var entries = logs.Count(log => string.Equals(log.Direction, "IN", StringComparison.OrdinalIgnoreCase));
        var exits = logs.Count(log => string.Equals(log.Direction, "OUT", StringComparison.OrdinalIgnoreCase));
        var exceptions = logs.Count(IsExceptionLog);
        var bypassCount = logs.Count(log => log.IsBypass == true);
        var vehicleInsideCount = await _context.Vehicles.AsNoTracking()
            .CountAsync(vehicle => vehicle.ParkingStatus != null && vehicle.ParkingStatus.ToUpper() == "IN");

        return Ok(new
        {
            generatedAt = DateTime.Now,
            totalToday = logs.Count,
            entriesToday = entries,
            exitsToday = exits,
            exceptionsToday = exceptions,
            bypassToday = bypassCount,
            faceDetectionsToday = logs.Count(log => !string.IsNullOrWhiteSpace(log.CapturedFaceImageUrl)),
            plateDetectionsToday = logs.Count(log => !string.IsNullOrWhiteSpace(log.CapturedLicensePlate)),
            vehiclesInside = vehicleInsideCount,
            successRate = logs.Count == 0
                ? 0
                : (int)Math.Round((logs.Count - exceptions) * 100.0 / logs.Count)
        });
    }

    [HttpGet("exceptions")]
    public async Task<IActionResult> GetExceptions(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? query = null,
        [FromQuery] int? reasonId = null,
        [FromQuery] DateTime? dateFrom = null,
        [FromQuery] DateTime? dateTo = null)
    {
        page = Math.Max(page, 1);
        pageSize = Math.Clamp(pageSize, 1, 100);

        var exceptionsQuery = BuildLogProjectionQuery()
            .Where(log =>
                log.IsBypass == true ||
                log.ExceptionReasonId != null ||
                (log.ResultStatus != null && !SuccessfulStatuses.Contains(log.ResultStatus.ToUpper())));

        if (!string.IsNullOrWhiteSpace(query))
        {
            var normalized = query.Trim();
            exceptionsQuery = exceptionsQuery.Where(log =>
                (log.ActorName != null && log.ActorName.Contains(normalized)) ||
                (log.CapturedLicensePlate != null && log.CapturedLicensePlate.Contains(normalized)) ||
                (log.Note != null && log.Note.Contains(normalized)));
        }

        if (reasonId.HasValue)
        {
            exceptionsQuery = exceptionsQuery.Where(log => log.ExceptionReasonId == reasonId.Value);
        }

        if (dateFrom.HasValue)
        {
            exceptionsQuery = exceptionsQuery.Where(log => log.Timestamp >= dateFrom.Value);
        }

        if (dateTo.HasValue)
        {
            var dateToExclusive = dateTo.Value.Date.AddDays(1);
            exceptionsQuery = exceptionsQuery.Where(log => log.Timestamp < dateToExclusive);
        }

        var total = await exceptionsQuery.CountAsync();
        var items = await exceptionsQuery
            .OrderByDescending(log => log.Timestamp)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        var summaryByReason = await exceptionsQuery
            .GroupBy(log => new { log.ExceptionReasonId, log.ExceptionReasonCode, log.ExceptionReasonDescription })
            .Select(group => new
            {
                reasonId = group.Key.ExceptionReasonId,
                reasonCode = group.Key.ExceptionReasonCode ?? "UNCLASSIFIED",
                reasonDescription = group.Key.ExceptionReasonDescription ?? "Chưa khai báo lý do",
                count = group.Count()
            })
            .OrderByDescending(item => item.count)
            .ToListAsync();

        return Ok(new
        {
            page,
            pageSize,
            total,
            items = items.Select(MapLogItem),
            summaryByReason
        });
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetDetail(int id)
    {
        var item = await BuildLogProjectionQuery()
            .FirstOrDefaultAsync(log => log.LogId == id);

        if (item == null)
        {
            return NotFound(new { message = $"Không tìm thấy bản ghi log #{id}" });
        }

        return Ok(MapLogItem(item));
    }

    private IQueryable<AccessLogListItem> BuildLogProjectionQuery()
    {
        return _context.AccessLogs.AsNoTracking()
            .Select(log => new AccessLogListItem
            {
                LogId = log.LogId,
                Timestamp = log.Timestamp,
                Direction = log.Direction,
                GateId = log.GateId,
                GateName = log.Gate != null ? log.Gate.GateName : null,
                CameraId = log.CameraId,
                CameraName = log.Camera != null ? log.Camera.CameraName : null,
                EmployeeId = log.EmployeeId,
                RegistrationId = log.RegistrationId,
                ActorName = log.Employee != null
                    ? log.Employee.FullName
                    : log.Registration != null && log.Registration.Guest != null
                        ? log.Registration.Guest.FullName
                        : "Chưa xác định",
                ActorType = log.Employee != null ? "Employee" : log.RegistrationId != null ? "Guest" : "Unknown",
                CapturedLicensePlate = log.CapturedLicensePlate,
                CapturedFaceImageUrl = log.CapturedFaceImageUrl,
                ResultStatus = log.ResultStatus,
                IsBypass = log.IsBypass,
                ExceptionReasonId = log.ExceptionReasonId,
                ExceptionReasonCode = log.ExceptionReason != null ? log.ExceptionReason.ReasonCode : null,
                ExceptionReasonDescription = log.ExceptionReason != null ? log.ExceptionReason.Description : null,
                Note = log.Note,
                EntryLogId = log.EntryLogId
            });
    }

    private static object MapLogItem(AccessLogListItem item)
    {
        return new
        {
            item.LogId,
            item.Timestamp,
            item.Direction,
            item.GateId,
            item.GateName,
            item.CameraId,
            item.CameraName,
            item.EmployeeId,
            item.RegistrationId,
            item.ActorName,
            item.ActorType,
            item.CapturedLicensePlate,
            item.CapturedFaceImageUrl,
            item.ResultStatus,
            item.IsBypass,
            item.ExceptionReasonId,
            item.ExceptionReasonCode,
            item.ExceptionReasonDescription,
            item.Note,
            item.EntryLogId,
            method = GetMethod(item),
            isException = IsExceptionLog(item)
        };
    }

    private static bool IsExceptionLog(dynamic log)
    {
        return log.IsBypass == true ||
               log.ExceptionReasonId != null ||
               (!string.IsNullOrWhiteSpace((string?)log.ResultStatus) &&
                !SuccessfulStatuses.Contains(((string)log.ResultStatus).ToUpper()));
    }

    private static string GetMethod(AccessLogListItem item)
    {
        if (item.IsBypass == true)
        {
            return "manual";
        }

        if (!string.IsNullOrWhiteSpace(item.CapturedFaceImageUrl) && !string.IsNullOrWhiteSpace(item.CapturedLicensePlate))
        {
            return "face-and-plate";
        }

        if (!string.IsNullOrWhiteSpace(item.CapturedFaceImageUrl))
        {
            return "face";
        }

        if (!string.IsNullOrWhiteSpace(item.CapturedLicensePlate))
        {
            return "plate";
        }

        return "system";
    }

    private sealed class AccessLogListItem
    {
        public int LogId { get; set; }
        public DateTime? Timestamp { get; set; }
        public string? Direction { get; set; }
        public int? GateId { get; set; }
        public string? GateName { get; set; }
        public int? CameraId { get; set; }
        public string? CameraName { get; set; }
        public int? EmployeeId { get; set; }
        public int? RegistrationId { get; set; }
        public string? ActorName { get; set; }
        public string? ActorType { get; set; }
        public string? CapturedLicensePlate { get; set; }
        public string? CapturedFaceImageUrl { get; set; }
        public string? ResultStatus { get; set; }
        public bool? IsBypass { get; set; }
        public int? ExceptionReasonId { get; set; }
        public string? ExceptionReasonCode { get; set; }
        public string? ExceptionReasonDescription { get; set; }
        public string? Note { get; set; }
        public int? EntryLogId { get; set; }
    }
}

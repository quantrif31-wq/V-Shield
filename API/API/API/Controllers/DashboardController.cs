using API.Data;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/dashboard")]
[Authorize]
public class DashboardController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public DashboardController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet("overview")]
    public async Task<IActionResult> GetOverview()
    {
        var today = DateTime.Today;
        var tomorrow = today.AddDays(1);
        var weekStart = StartOfWeek(today, DayOfWeek.Monday);
        var weekEnd = weekStart.AddDays(7);

        // NOTE: All queries must be awaited sequentially because DbContext is NOT thread-safe.
        // Using Task.WhenAll with the same DbContext causes InvalidOperationException.

        var vehiclesInside = await _context.Vehicles.AsNoTracking()
            .CountAsync(v => v.ParkingStatus != null && v.ParkingStatus.ToUpper() == "IN");

        var expectedVisitorsToday = await _context.PreRegistrations.AsNoTracking()
            .CountAsync(r => r.ExpectedTimeIn >= today && r.ExpectedTimeIn < tomorrow);

        var pendingRegistrations = await _context.PreRegistrations.AsNoTracking()
            .CountAsync(r => r.Status != null && r.Status.ToUpper() == "PENDING");

        var camerasConfigured = await _context.Cameras.AsNoTracking().CountAsync();
        var gatesConfigured = await _context.Gates.AsNoTracking().CountAsync();
        var guestProfiles = await _context.GuestProfiles.AsNoTracking().CountAsync();

        var employeeCount = await _context.Employees.AsNoTracking().CountAsync();
        var trainedEmployeeCount = await _context.EmployeeFaceModels.AsNoTracking()
            .Select(m => m.EmployeeId)
            .Distinct()
            .CountAsync();

        var todaysLogs = await _context.AccessLogs.AsNoTracking()
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

        var weeklyLogs = await _context.AccessLogs.AsNoTracking()
            .Where(log => log.Timestamp >= weekStart && log.Timestamp < weekEnd)
            .Select(log => new
            {
                log.Timestamp,
                log.Direction
            })
            .ToListAsync();

        var recentActivitiesRaw = await _context.AccessLogs.AsNoTracking()
            .OrderByDescending(log => log.Timestamp)
            .Take(6)
            .Select(log => new
            {
                log.LogId,
                log.Timestamp,
                log.Direction,
                log.CapturedLicensePlate,
                log.ResultStatus,
                log.IsBypass,
                log.Note,
                GateName = log.Gate != null ? log.Gate.GateName : null,
                CameraName = log.Camera != null ? log.Camera.CameraName : null,
                EmployeeName = log.Employee != null ? log.Employee.FullName : null,
                GuestName = log.Registration != null && log.Registration.Guest != null ? log.Registration.Guest.FullName : null,
                ExceptionReason = log.ExceptionReason != null ? log.ExceptionReason.Description : null
            })
            .ToListAsync();
        var successfulStatuses = new[] { "APPROVED", "SUCCESS", "GRANTED", "OK", "MATCHED" };

        var traffic = Enumerable.Range(0, 7)
            .Select(offset =>
            {
                var day = weekStart.AddDays(offset);
                var nextDay = day.AddDays(1);
                var dayLogs = weeklyLogs
                    .Where(log => log.Timestamp >= day && log.Timestamp < nextDay)
                    .ToList();

                return new
                {
                    label = GetWeekdayLabel(day.DayOfWeek),
                    date = day,
                    checkIn = dayLogs.Count(log => string.Equals(log.Direction, "IN", StringComparison.OrdinalIgnoreCase)),
                    checkOut = dayLogs.Count(log => string.Equals(log.Direction, "OUT", StringComparison.OrdinalIgnoreCase))
                };
            })
            .ToList();

        var dailyIn = todaysLogs.Count(log => string.Equals(log.Direction, "IN", StringComparison.OrdinalIgnoreCase));
        var dailyOut = todaysLogs.Count(log => string.Equals(log.Direction, "OUT", StringComparison.OrdinalIgnoreCase));
        var dailyExceptions = todaysLogs.Count(log =>
            log.IsBypass == true ||
            log.ExceptionReasonId != null ||
            (!string.IsNullOrWhiteSpace(log.ResultStatus) && !successfulStatuses.Contains(log.ResultStatus.ToUpper())));

        var recognitionCoverage = employeeCount == 0
            ? 0
            : (int)Math.Round(trainedEmployeeCount * 100.0 / employeeCount);

        var recentActivities = recentActivitiesRaw.Select(activity => new
        {
            activity.LogId,
            activity.Timestamp,
            activity.Direction,
            actorName = activity.EmployeeName ?? activity.GuestName ?? "Chưa xác định",
            gateName = activity.GateName ?? "Chưa gán cổng",
            cameraName = activity.CameraName,
            activity.CapturedLicensePlate,
            activity.ResultStatus,
            activity.IsBypass,
            activity.Note,
            activity.ExceptionReason,
            actorType = activity.EmployeeName != null ? "Employee" : activity.GuestName != null ? "Guest" : "Unknown"
        });

        return Ok(new
        {
            snapshot = new
            {
                generatedAt = DateTime.Now,
                vehiclesInside,
                expectedVisitorsToday,
                pendingRegistrations,
                dailyCheckIn = dailyIn,
                dailyCheckOut = dailyOut,
                dailyExceptions,
                camerasConfigured,
                gatesConfigured,
                guestProfiles,
                employeeCount,
                trainedEmployeeCount,
                recognitionCoverage
            },
            weeklyTraffic = traffic,
            recentActivities
        });
    }

    private static DateTime StartOfWeek(DateTime value, DayOfWeek startOfWeek)
    {
        var diff = (7 + (value.DayOfWeek - startOfWeek)) % 7;
        return value.AddDays(-1 * diff).Date;
    }

    private static string GetWeekdayLabel(DayOfWeek dayOfWeek)
    {
        return dayOfWeek switch
        {
            DayOfWeek.Monday => "T2",
            DayOfWeek.Tuesday => "T3",
            DayOfWeek.Wednesday => "T4",
            DayOfWeek.Thursday => "T5",
            DayOfWeek.Friday => "T6",
            DayOfWeek.Saturday => "T7",
            _ => "CN"
        };
    }
}

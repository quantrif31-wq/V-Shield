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

        var vehiclesInsideTask = _context.Vehicles.AsNoTracking()
            .CountAsync(v => v.ParkingStatus != null && v.ParkingStatus.ToUpper() == "IN");

        var expectedVisitorsTodayTask = _context.PreRegistrations.AsNoTracking()
            .CountAsync(r => r.ExpectedTimeIn >= today && r.ExpectedTimeIn < tomorrow);

        var pendingRegistrationsTask = _context.PreRegistrations.AsNoTracking()
            .CountAsync(r => r.Status != null && r.Status.ToUpper() == "PENDING");

        var camerasConfiguredTask = _context.Cameras.AsNoTracking().CountAsync();
        var gatesConfiguredTask = _context.Gates.AsNoTracking().CountAsync();
        var guestProfilesTask = _context.GuestProfiles.AsNoTracking().CountAsync();

        var employeeCountTask = _context.Employees.AsNoTracking().CountAsync();
        var trainedEmployeeCountTask = _context.EmployeeFaceModels.AsNoTracking()
            .Select(m => m.EmployeeId)
            .Distinct()
            .CountAsync();

        var todaysLogsTask = _context.AccessLogs.AsNoTracking()
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

        var weeklyLogsTask = _context.AccessLogs.AsNoTracking()
            .Where(log => log.Timestamp >= weekStart && log.Timestamp < weekEnd)
            .Select(log => new
            {
                log.Timestamp,
                log.Direction
            })
            .ToListAsync();

        var recentActivitiesTask = _context.AccessLogs.AsNoTracking()
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

        await Task.WhenAll(
            vehiclesInsideTask,
            expectedVisitorsTodayTask,
            pendingRegistrationsTask,
            camerasConfiguredTask,
            gatesConfiguredTask,
            guestProfilesTask,
            employeeCountTask,
            trainedEmployeeCountTask,
            todaysLogsTask,
            weeklyLogsTask,
            recentActivitiesTask
        );

        var todaysLogs = todaysLogsTask.Result;
        var successfulStatuses = new[] { "APPROVED", "SUCCESS", "GRANTED", "OK", "MATCHED" };

        var traffic = Enumerable.Range(0, 7)
            .Select(offset =>
            {
                var day = weekStart.AddDays(offset);
                var nextDay = day.AddDays(1);
                var dayLogs = weeklyLogsTask.Result
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

        var recognitionCoverage = employeeCountTask.Result == 0
            ? 0
            : (int)Math.Round(trainedEmployeeCountTask.Result * 100.0 / employeeCountTask.Result);

        var recentActivities = recentActivitiesTask.Result.Select(activity => new
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
                vehiclesInside = vehiclesInsideTask.Result,
                expectedVisitorsToday = expectedVisitorsTodayTask.Result,
                pendingRegistrations = pendingRegistrationsTask.Result,
                dailyCheckIn = dailyIn,
                dailyCheckOut = dailyOut,
                dailyExceptions,
                camerasConfigured = camerasConfiguredTask.Result,
                gatesConfigured = gatesConfiguredTask.Result,
                guestProfiles = guestProfilesTask.Result,
                employeeCount = employeeCountTask.Result,
                trainedEmployeeCount = trainedEmployeeCountTask.Result,
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

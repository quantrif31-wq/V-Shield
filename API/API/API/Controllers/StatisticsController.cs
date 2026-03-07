using API.Data;
using API.DTOs;
using API.Hubs;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class StatisticsController : ControllerBase
{
    private readonly ApplicationDbContext _context;
    private readonly IHubContext<EmployeeStatsHub> _hubContext;

    public StatisticsController(ApplicationDbContext context, IHubContext<EmployeeStatsHub> hubContext)
    {
        _context = context;
        _hubContext = hubContext;
    }

    /// <summary>
    /// Thống kê tổng số nhân viên trong hệ thống:
    /// tổng, đang hoạt động, ngưng hoạt động, theo phòng ban, theo chức vụ.
    /// </summary>
    [HttpGet("employees/summary")]
    public async Task<IActionResult> GetSummary()
    {
        var employees = await _context.Employees
            .Include(e => e.Department)
            .Include(e => e.Position)
            .ToListAsync();

        var byDept = employees
            .GroupBy(e => new { e.DepartmentId, Name = e.Department?.Name })
            .Select(g => new DepartmentStatItem
            {
                DepartmentId = g.Key.DepartmentId,
                DepartmentName = g.Key.Name ?? "Chưa phân phòng",
                TotalCount = g.Count(),
                ActiveCount = g.Count(e => e.Status == true)
            })
            .OrderByDescending(x => x.TotalCount)
            .ToList();

        var byPos = employees
            .GroupBy(e => new { e.PositionId, Name = e.Position?.Name })
            .Select(g => new PositionStatItem
            {
                PositionId = g.Key.PositionId,
                PositionName = g.Key.Name ?? "Chưa có chức vụ",
                TotalCount = g.Count(),
                ActiveCount = g.Count(e => e.Status == true)
            })
            .OrderByDescending(x => x.TotalCount)
            .ToList();

        return Ok(new EmployeeSummaryResponse
        {
            TotalEmployees = employees.Count,
            ActiveEmployees = employees.Count(e => e.Status == true),
            InactiveEmployees = employees.Count(e => e.Status != true),
            ByDepartment = byDept,
            ByPosition = byPos,
            CalculatedAt = DateTime.Now
        });
    }

    /// <summary>
    /// SSE stream: push số lượng nhân viên mỗi 5 giây (real-time polling).
    /// Client kết nối một lần, tự động nhận dữ liệu mới mà không cần gọi lại API.
    /// </summary>
    [HttpGet("employees/stream")]
    public async Task StreamEmployeeCount(CancellationToken cancellationToken)
    {
        Response.ContentType = "text/event-stream";
        Response.Headers["Cache-Control"] = "no-cache";
        Response.Headers["X-Accel-Buffering"] = "no";

        while (!cancellationToken.IsCancellationRequested)
        {
            int total = await _context.Employees.CountAsync(cancellationToken);
            int active = await _context.Employees.CountAsync(e => e.Status == true, cancellationToken);

            var data = System.Text.Json.JsonSerializer.Serialize(new
            {
                totalEmployees = total,
                activeEmployees = active,
                inactiveEmployees = total - active,
                timestamp = DateTime.Now
            });

            await Response.WriteAsync($"data: {data}\n\n", cancellationToken);
            await Response.Body.FlushAsync(cancellationToken);

            await Task.Delay(TimeSpan.FromSeconds(5), cancellationToken);
        }
    }
}

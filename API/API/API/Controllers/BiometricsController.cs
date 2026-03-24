using API.Data;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/biometrics")]
[Authorize]
public class BiometricsController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public BiometricsController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet("overview")]
    public async Task<IActionResult> GetOverview([FromQuery] string? query = null)
    {
        var employeesQuery = _context.Employees.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(query))
        {
            var normalized = query.Trim();
            employeesQuery = employeesQuery.Where(employee =>
                employee.FullName.Contains(normalized) ||
                (employee.Email != null && employee.Email.Contains(normalized)) ||
                (employee.Phone != null && employee.Phone.Contains(normalized)) ||
                (employee.Department != null && employee.Department.Name.Contains(normalized)) ||
                (employee.Position != null && employee.Position.Name.Contains(normalized)));
        }

        var employees = await employeesQuery
            .OrderBy(employee => employee.FullName)
            .Select(employee => new
            {
                employee.EmployeeId,
                employee.FullName,
                employee.Email,
                employee.Phone,
                employee.FaceImageUrl,
                employee.Status,
                DepartmentName = employee.Department != null ? employee.Department.Name : null,
                PositionName = employee.Position != null ? employee.Position.Name : null,
                vehicleCount = employee.Vehicles.Count(),
                videoCount = _context.EmployeeFaceVideos.Count(video => video.EmployeeId == employee.EmployeeId),
                modelCount = _context.EmployeeFaceModels.Count(model => model.EmployeeId == employee.EmployeeId),
                latestVideoAt = _context.EmployeeFaceVideos
                    .Where(video => video.EmployeeId == employee.EmployeeId)
                    .OrderByDescending(video => video.CreatedAt)
                    .Select(video => (DateTime?)video.CreatedAt)
                    .FirstOrDefault(),
                latestVideoPath = _context.EmployeeFaceVideos
                    .Where(video => video.EmployeeId == employee.EmployeeId)
                    .OrderByDescending(video => video.CreatedAt)
                    .Select(video => video.FilePath)
                    .FirstOrDefault(),
                latestModelAt = _context.EmployeeFaceModels
                    .Where(model => model.EmployeeId == employee.EmployeeId)
                    .OrderByDescending(model => model.CreatedAt)
                    .Select(model => (DateTime?)model.CreatedAt)
                    .FirstOrDefault(),
                latestModelPath = _context.EmployeeFaceModels
                    .Where(model => model.EmployeeId == employee.EmployeeId)
                    .OrderByDescending(model => model.CreatedAt)
                    .Select(model => model.ModelPath)
                    .FirstOrDefault()
            })
            .ToListAsync();

        var recentVideos = await _context.EmployeeFaceVideos.AsNoTracking()
            .OrderByDescending(video => video.CreatedAt)
            .Take(10)
            .Select(video => new
            {
                video.Id,
                video.EmployeeId,
                employeeName = video.Employee.FullName,
                video.FileName,
                video.FilePath,
                video.FileSize,
                video.CreatedAt
            })
            .ToListAsync();

        var recentModels = await _context.EmployeeFaceModels.AsNoTracking()
            .OrderByDescending(model => model.CreatedAt)
            .Take(10)
            .Select(model => new
            {
                model.Id,
                model.EmployeeId,
                employeeName = model.Employee.FullName,
                model.ModelFileName,
                model.ModelPath,
                model.CreatedAt
            })
            .ToListAsync();

        var trainedEmployees = employees.Count(employee => employee.modelCount > 0);
        var employeesWithVideos = employees.Count(employee => employee.videoCount > 0);

        return Ok(new
        {
            generatedAt = DateTime.Now,
            summary = new
            {
                totalEmployees = employees.Count,
                trainedEmployees,
                employeesWithVideos,
                employeesMissingModels = employees.Count - trainedEmployees,
                employeesMissingVideos = employees.Count - employeesWithVideos,
                totalModelFiles = recentModels.Count == 0
                    ? await _context.EmployeeFaceModels.AsNoTracking().CountAsync()
                    : employees.Sum(employee => employee.modelCount),
                totalVideoFiles = recentVideos.Count == 0
                    ? await _context.EmployeeFaceVideos.AsNoTracking().CountAsync()
                    : employees.Sum(employee => employee.videoCount)
            },
            employees,
            recentVideos,
            recentModels
        });
    }
}

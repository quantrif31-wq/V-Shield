using API.Data;
using API.DTOs.PreRegistration;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/registration-links")]
public class RegistrationLinkController : ControllerBase
{
    private readonly ApplicationDbContext _context;
    private readonly IConfiguration _config;

    public RegistrationLinkController(ApplicationDbContext context, IConfiguration config)
    {
        _context = context;
        _config = config;
    }

    [HttpPost]
    [Authorize]
    public async Task<IActionResult> CreateLink([FromBody] CreateLinkRequestDto dto)
    {
        var employee = await _context.Employees.FindAsync(dto.HostEmployeeId);
        if (employee == null)
            return NotFound(new { Message = "Không tìm thấy nhân viên" });

        // Tạo token 32 ký tự không dấu gạch, khó đoán
        var token = Guid.NewGuid().ToString("N");

        var link = new RegistrationLink
        {
            Token = token,
            HostEmployeeId = dto.HostEmployeeId,
            ExpiredAt = DateTime.Now.AddHours(dto.ExpiryHours),
            IsUsed = false,
            CreatedAt = DateTime.Now
        };

        _context.RegistrationLinks.Add(link);
        await _context.SaveChangesAsync();

        var frontendUrl = (_config["AppSettings:FrontendUrl"] ?? $"{Request.Scheme}://{Request.Host}").TrimEnd('/');

        return Ok(new CreateLinkResponseDto
        {
            Token = token,
            RegistrationUrl = $"{frontendUrl}/register/{token}",
            ExpiredAt = link.ExpiredAt
        });
    }

    [HttpGet]
    [Authorize]
    public async Task<IActionResult> GetLinks([FromQuery] string? query = null)
    {
        var linksQuery = _context.RegistrationLinks
            .AsNoTracking()
            .Include(link => link.HostEmployee)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(query))
        {
            var normalized = query.Trim();
            linksQuery = linksQuery.Where(link =>
                link.Token.Contains(normalized) ||
                link.HostEmployee.FullName.Contains(normalized));
        }

        var now = DateTime.Now;
        var frontendUrl = (_config["AppSettings:FrontendUrl"] ?? $"{Request.Scheme}://{Request.Host}").TrimEnd('/');

        var items = await linksQuery
            .OrderByDescending(link => link.CreatedAt)
            .Select(link => new
            {
                link.LinkId,
                link.Token,
                link.HostEmployeeId,
                hostEmployeeName = link.HostEmployee.FullName,
                link.ExpiredAt,
                link.IsUsed,
                link.CreatedAt,
                isExpired = link.ExpiredAt < now,
                registrationUrl = $"{frontendUrl}/register/{link.Token}"
            })
            .ToListAsync();

        return Ok(items);
    }
}

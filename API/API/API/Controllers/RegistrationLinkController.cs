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

        var frontendUrl = _config["AppSettings:FrontendUrl"];

        return Ok(new CreateLinkResponseDto
        {
            Token = token,
            RegistrationUrl = $"{frontendUrl}/register/{token}",
            ExpiredAt = link.ExpiredAt
        });
    }
}

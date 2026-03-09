using API.Data;
using API.DTOs.PreRegistration;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/pre-registrations")]
public class PreRegistrationController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public PreRegistrationController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet("validate/{token}")]
    [AllowAnonymous]
    public async Task<IActionResult> ValidateToken(string token)
    {
        var link = await _context.RegistrationLinks
            .Include(l => l.HostEmployee)
            .FirstOrDefaultAsync(l => l.Token == token);

        if (link == null)
            return NotFound(new { Message = "Link không tồn tại" });

        if (link.IsUsed)
            return BadRequest(new { Message = "Link đã được sử dụng" });

        if (link.ExpiredAt < DateTime.Now)
            return BadRequest(new { Message = "Link đã hết hạn", ExpiredAt = link.ExpiredAt });

        return Ok(new ValidateTokenResponseDto
        {
            HostEmployeeName = link.HostEmployee.FullName,
            ExpiredAt = link.ExpiredAt
        });
    }

    [HttpPost("submit/{token}")]
    [AllowAnonymous]
    public async Task<IActionResult> SubmitRegistration(
        string token,
        [FromBody] SubmitRegistrationDto dto)
    {
        // 1. Validate token
        var link = await _context.RegistrationLinks
            .FirstOrDefaultAsync(l => l.Token == token);

        if (link == null || link.IsUsed || link.ExpiredAt < DateTime.Now)
            return BadRequest(new { Message = "Link không hợp lệ hoặc đã hết hạn" });

        // 2. Validate thời gian
        if (dto.ExpectedTimeOut <= dto.ExpectedTimeIn)
            return BadRequest(new { Message = "Thời gian ra phải sau thời gian vào" });

        // 3. Validate ảnh base64
        if (!string.IsNullOrEmpty(dto.FaceImageBase64)
            && !IsValidBase64Image(dto.FaceImageBase64))
            return BadRequest(new { Message = "Ảnh mặt không hợp lệ. Cần format: data:image/jpeg;base64,..." });

        if (!string.IsNullOrEmpty(dto.LicensePlateImageBase64)
            && !IsValidBase64Image(dto.LicensePlateImageBase64))
            return BadRequest(new { Message = "Ảnh biển số không hợp lệ. Cần format: data:image/jpeg;base64,..." });

        // 4. Tìm hoặc tạo GuestProfile theo SĐT
        GuestProfile guest;

        if (!string.IsNullOrEmpty(dto.Phone))
        {
            guest = await _context.GuestProfiles
                        .FirstOrDefaultAsync(g => g.Phone == dto.Phone)
                    ?? new GuestProfile();
        }
        else
        {
            guest = new GuestProfile();
        }

        // Cập nhật thông tin guest
        guest.FullName = dto.FullName;
        guest.Phone = dto.Phone;

        // Biển số mặc định: chỉ set lần đầu, không override
        if (string.IsNullOrEmpty(guest.DefaultLicensePlate))
            guest.DefaultLicensePlate = dto.ExpectedLicensePlate;

        // Ảnh mặt: cập nhật nếu có ảnh mới
        if (!string.IsNullOrEmpty(dto.FaceImageBase64))
            guest.FaceImageUrl = dto.FaceImageBase64;

        if (guest.GuestId == 0)
            _context.GuestProfiles.Add(guest);

        await _context.SaveChangesAsync(); // Cần GuestId cho bước tiếp

        // 5. Tạo PreRegistration
        var preReg = new PreRegistration
        {
            GuestId = guest.GuestId,
            HostEmployeeId = link.HostEmployeeId,
            ExpectedLicensePlate = dto.ExpectedLicensePlate,
            LicensePlateImageBase64 = dto.LicensePlateImageBase64,
            ExpectedTimeIn = dto.ExpectedTimeIn,
            ExpectedTimeOut = dto.ExpectedTimeOut,
            NumberOfVisitors = dto.NumberOfVisitors,
            Status = "Pending",
            CreatedAt = DateTime.Now
        };

        _context.PreRegistrations.Add(preReg);
        await _context.SaveChangesAsync(); // Cần RegistrationId cho VisitorDetail

        // 6. Lưu danh sách khách trong đoàn
        if (dto.Visitors.Any())
        {
            var visitors = dto.Visitors.Select(v => new VisitorDetail
            {
                RegistrationId = preReg.RegistrationId,
                FullName = v.FullName,
                IdCardNumber = v.IdCardNumber
            });

            _context.VisitorDetails.AddRange(visitors);
        }

        // 7. Đánh dấu link đã dùng
        link.IsUsed = true;

        await _context.SaveChangesAsync();

        return Ok(new
        {
            Message = "Đăng ký thành công! Vui lòng chờ xác nhận.",
            RegistrationId = preReg.RegistrationId
        });
    }

    [HttpGet]
    [Authorize]
    public async Task<IActionResult> GetAll(
        [FromQuery] string? status,
        [FromQuery] DateTime? date,
        [FromQuery] int? hostEmployeeId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20)
    {
        var query = _context.PreRegistrations
            .Include(r => r.Guest)
            .Include(r => r.HostEmployee)
            .AsQueryable();

        if (!string.IsNullOrEmpty(status))
            query = query.Where(r => r.Status == status);

        if (date.HasValue)
            query = query.Where(r => r.ExpectedTimeIn.Date == date.Value.Date);

        if (hostEmployeeId.HasValue)
            query = query.Where(r => r.HostEmployeeId == hostEmployeeId);

        var total = await query.CountAsync();

        var items = await query
            .OrderByDescending(r => r.CreatedAt)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(r => new RegistrationListItemDto
            {
                RegistrationId = r.RegistrationId,
                GuestId = r.Guest!.GuestId,
                GuestFullName = r.Guest.FullName,
                GuestPhone = r.Guest.Phone,
                ExpectedLicensePlate = r.ExpectedLicensePlate,
                ExpectedTimeIn = r.ExpectedTimeIn,
                ExpectedTimeOut = r.ExpectedTimeOut,
                NumberOfVisitors = r.NumberOfVisitors,
                Status = r.Status,
                HostEmployeeName = r.HostEmployee!.FullName,
                CreatedAt = r.CreatedAt
            })
            .ToListAsync();

        return Ok(new
        {
            Total = total,
            Page = page,
            PageSize = pageSize,
            Items = items
        });
    }

    [HttpGet("{id}")]
    [Authorize]
    public async Task<IActionResult> GetDetail(int id)
    {
        var reg = await _context.PreRegistrations
            .Include(r => r.Guest)
            .Include(r => r.HostEmployee)
            .Include(r => r.VisitorDetails)
            .Include(r => r.AccessLogs)
            .FirstOrDefaultAsync(r => r.RegistrationId == id);

        if (reg == null)
            return NotFound(new { Message = "Không tìm thấy đơn đăng ký" });

        return Ok(new RegistrationDetailDto
        {
            RegistrationId = reg.RegistrationId,
            GuestId = reg.Guest!.GuestId,
            GuestFullName = reg.Guest.FullName,
            GuestPhone = reg.Guest.Phone,
            ExpectedLicensePlate = reg.ExpectedLicensePlate,
            ExpectedTimeIn = reg.ExpectedTimeIn,
            ExpectedTimeOut = reg.ExpectedTimeOut,
            NumberOfVisitors = reg.NumberOfVisitors,
            Status = reg.Status,
            HostEmployeeName = reg.HostEmployee!.FullName,
            CreatedAt = reg.CreatedAt,

            // Ảnh mặt từ GuestProfile — dùng chung cho mọi lần đăng ký
            FaceImageUrl = reg.Guest.FaceImageUrl,

            // Ảnh biển số từ PreRegistration — riêng cho lần này
            LicensePlateImageBase64 = reg.LicensePlateImageBase64,

            Visitors = reg.VisitorDetails.Select(v => new VisitorInfoDto
            {
                FullName = v.FullName,
                IdCardNumber = v.IdCardNumber
            }).ToList(),

            AccessLogs = reg.AccessLogs
    .OrderBy(l => l.Timestamp)
    .Select(l => new AccessLogDto
    {
        LogId = l.LogId,
        Timestamp = l.Timestamp,
        Direction = l.Direction,   // "IN" / "OUT"
        CapturedLicensePlate = l.CapturedLicensePlate,
        ResultStatus = l.ResultStatus,
        Note = l.Note
    }).ToList()
        });
    }

    [HttpPatch("{id}/status")]
    [Authorize]
    public async Task<IActionResult> UpdateStatus(int id, [FromBody] UpdateStatusDto dto)
    {
        var reg = await _context.PreRegistrations.FindAsync(id);

        if (reg == null)
            return NotFound(new { Message = "Không tìm thấy đơn đăng ký" });

        if (reg.Status is "Approved" or "Rejected")
            return BadRequest(new { Message = $"Đơn đã được xử lý ({reg.Status}), không thể thay đổi" });

        reg.Status = dto.Status;
        await _context.SaveChangesAsync();

        return Ok(new { Message = $"Đã cập nhật trạng thái thành '{dto.Status}'" });
    }

    private static bool IsValidBase64Image(string base64)
    {
        if (!base64.StartsWith("data:image/")) return false;
        try
        {
            var comma = base64.IndexOf(',');
            if (comma < 0) return false;
            Convert.FromBase64String(base64[(comma + 1)..]);
            return true;
        }
        catch { return false; }
    }
}

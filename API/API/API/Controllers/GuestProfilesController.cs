using API.Data;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/guest-profiles")]
[Authorize]
public class GuestProfilesController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public GuestProfilesController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? query = null)
    {
        page = Math.Max(page, 1);
        pageSize = Math.Clamp(pageSize, 1, 100);

        var guestsQuery = _context.GuestProfiles.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(query))
        {
            var normalized = query.Trim();
            guestsQuery = guestsQuery.Where(guest =>
                guest.FullName.Contains(normalized) ||
                (guest.Phone != null && guest.Phone.Contains(normalized)) ||
                (guest.DefaultLicensePlate != null && guest.DefaultLicensePlate.Contains(normalized)));
        }

        var total = await guestsQuery.CountAsync();
        var items = await guestsQuery
            .OrderBy(guest => guest.FullName)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(guest => new
            {
                guest.GuestId,
                guest.FullName,
                guest.Phone,
                guest.DefaultLicensePlate,
                guest.FaceImageUrl,
                preRegistrationCount = guest.PreRegistrations.Count(),
                lastRegistrationAt = guest.PreRegistrations
                    .OrderByDescending(registration => registration.CreatedAt)
                    .Select(registration => (DateTime?)registration.CreatedAt)
                    .FirstOrDefault(),
                nextExpectedVisit = guest.PreRegistrations
                    .Where(registration => registration.ExpectedTimeIn >= DateTime.Today)
                    .OrderBy(registration => registration.ExpectedTimeIn)
                    .Select(registration => (DateTime?)registration.ExpectedTimeIn)
                    .FirstOrDefault()
            })
            .ToListAsync();

        return Ok(new
        {
            page,
            pageSize,
            total,
            items
        });
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetDetail(int id)
    {
        var guest = await _context.GuestProfiles.AsNoTracking()
            .Where(item => item.GuestId == id)
            .Select(item => new
            {
                item.GuestId,
                item.FullName,
                item.Phone,
                item.DefaultLicensePlate,
                item.FaceImageUrl,
                preRegistrations = item.PreRegistrations
                    .OrderByDescending(registration => registration.CreatedAt)
                    .Select(registration => new
                    {
                        registration.RegistrationId,
                        registration.ExpectedTimeIn,
                        registration.ExpectedTimeOut,
                        registration.Status,
                        registration.ExpectedLicensePlate,
                        registration.NumberOfVisitors,
                        hostEmployeeName = registration.HostEmployee != null ? registration.HostEmployee.FullName : null
                    })
                    .ToList()
            })
            .FirstOrDefaultAsync();

        if (guest == null)
        {
            return NotFound(new { message = $"Không tìm thấy hồ sơ khách #{id}" });
        }

        return Ok(guest);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] UpsertGuestProfileRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.FullName))
        {
            return BadRequest(new { message = "Họ tên khách là bắt buộc" });
        }

        var guest = new GuestProfile
        {
            FullName = request.FullName.Trim(),
            Phone = NormalizeOptional(request.Phone),
            DefaultLicensePlate = NormalizeOptional(request.DefaultLicensePlate),
            FaceImageUrl = NormalizeOptional(request.FaceImageUrl)
        };

        _context.GuestProfiles.Add(guest);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetDetail), new { id = guest.GuestId }, new
        {
            guest.GuestId,
            guest.FullName,
            guest.Phone,
            guest.DefaultLicensePlate,
            guest.FaceImageUrl
        });
    }

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpsertGuestProfileRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.FullName))
        {
            return BadRequest(new { message = "Họ tên khách là bắt buộc" });
        }

        var guest = await _context.GuestProfiles.FindAsync(id);
        if (guest == null)
        {
            return NotFound(new { message = $"Không tìm thấy hồ sơ khách #{id}" });
        }

        guest.FullName = request.FullName.Trim();
        guest.Phone = NormalizeOptional(request.Phone);
        guest.DefaultLicensePlate = NormalizeOptional(request.DefaultLicensePlate);
        guest.FaceImageUrl = NormalizeOptional(request.FaceImageUrl);

        await _context.SaveChangesAsync();

        return Ok(new
        {
            guest.GuestId,
            guest.FullName,
            guest.Phone,
            guest.DefaultLicensePlate,
            guest.FaceImageUrl
        });
    }

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        var guest = await _context.GuestProfiles
            .Include(item => item.PreRegistrations)
            .FirstOrDefaultAsync(item => item.GuestId == id);

        if (guest == null)
        {
            return NotFound(new { message = $"Không tìm thấy hồ sơ khách #{id}" });
        }

        if (guest.PreRegistrations.Any())
        {
            return BadRequest(new
            {
                message = $"Không thể xóa hồ sơ khách đang có {guest.PreRegistrations.Count} lượt đăng ký liên quan"
            });
        }

        _context.GuestProfiles.Remove(guest);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    private static string? NormalizeOptional(string? value)
    {
        return string.IsNullOrWhiteSpace(value) ? null : value.Trim();
    }

    public sealed class UpsertGuestProfileRequest
    {
        public string FullName { get; set; } = string.Empty;
        public string? Phone { get; set; }
        public string? DefaultLicensePlate { get; set; }
        public string? FaceImageUrl { get; set; }
    }
}

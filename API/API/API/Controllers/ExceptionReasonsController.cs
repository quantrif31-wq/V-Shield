using API.Data;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/exception-reasons")]
[Authorize]
public class ExceptionReasonsController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public ExceptionReasonsController(ApplicationDbContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var items = await _context.ExceptionReasons.AsNoTracking()
            .OrderBy(reason => reason.ReasonCode)
            .Select(reason => new
            {
                reason.ReasonId,
                reason.ReasonCode,
                reason.Description,
                usageCount = reason.AccessLogs.Count()
            })
            .ToListAsync();

        return Ok(items);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Create([FromBody] UpsertExceptionReasonRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.ReasonCode) || string.IsNullOrWhiteSpace(request.Description))
        {
            return BadRequest(new { message = "Mã lý do và mô tả là bắt buộc" });
        }

        var normalizedCode = request.ReasonCode.Trim().ToUpper();
        var exists = await _context.ExceptionReasons.AnyAsync(reason => reason.ReasonCode.ToUpper() == normalizedCode);
        if (exists)
        {
            return Conflict(new { message = $"Mã lý do '{normalizedCode}' đã tồn tại" });
        }

        var reason = new ExceptionReason
        {
            ReasonCode = normalizedCode,
            Description = request.Description.Trim()
        };

        _context.ExceptionReasons.Add(reason);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetAll), new { id = reason.ReasonId }, new
        {
            reason.ReasonId,
            reason.ReasonCode,
            reason.Description
        });
    }

    [HttpPut("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Update(int id, [FromBody] UpsertExceptionReasonRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.ReasonCode) || string.IsNullOrWhiteSpace(request.Description))
        {
            return BadRequest(new { message = "Mã lý do và mô tả là bắt buộc" });
        }

        var normalizedCode = request.ReasonCode.Trim().ToUpper();
        var reason = await _context.ExceptionReasons.FindAsync(id);
        if (reason == null)
        {
            return NotFound(new { message = $"Không tìm thấy lý do ngoại lệ #{id}" });
        }

        var duplicate = await _context.ExceptionReasons.AnyAsync(item =>
            item.ReasonId != id && item.ReasonCode.ToUpper() == normalizedCode);

        if (duplicate)
        {
            return Conflict(new { message = $"Mã lý do '{normalizedCode}' đã tồn tại" });
        }

        reason.ReasonCode = normalizedCode;
        reason.Description = request.Description.Trim();

        await _context.SaveChangesAsync();

        return Ok(new
        {
            reason.ReasonId,
            reason.ReasonCode,
            reason.Description
        });
    }

    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        var reason = await _context.ExceptionReasons
            .Include(item => item.AccessLogs)
            .FirstOrDefaultAsync(item => item.ReasonId == id);

        if (reason == null)
        {
            return NotFound(new { message = $"Không tìm thấy lý do ngoại lệ #{id}" });
        }

        if (reason.AccessLogs.Any())
        {
            return BadRequest(new
            {
                message = $"Không thể xóa lý do đang được dùng bởi {reason.AccessLogs.Count} bản ghi ngoại lệ"
            });
        }

        _context.ExceptionReasons.Remove(reason);
        await _context.SaveChangesAsync();

        return NoContent();
    }

    public sealed class UpsertExceptionReasonRequest
    {
        public string ReasonCode { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
    }
}

using API.Data;
using API.DTOs;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class PositionsController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public PositionsController(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <summary>Lấy danh sách tất cả chức vụ (chỉ Admin)</summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var positions = await _context.Positions
            .OrderBy(p => p.PositionId)
            .Select(p => new PositionResponse
            {
                PositionId = p.PositionId,
                Name = p.Name,
                EmployeeCount = p.Employees.Count
            })
            .ToListAsync();

        return Ok(positions);
    }

    /// <summary>Lấy thông tin chức vụ theo ID (chỉ Admin)</summary>
    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var position = await _context.Positions
            .Include(p => p.Employees)
            .FirstOrDefaultAsync(p => p.PositionId == id);

        if (position == null)
            return NotFound(new { message = $"Không tìm thấy chức vụ ID {id}" });

        return Ok(new PositionResponse
        {
            PositionId = position.PositionId,
            Name = position.Name,
            EmployeeCount = position.Employees.Count
        });
    }

    /// <summary>Tạo chức vụ mới (chỉ Admin)</summary>
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreatePositionRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        // Kiểm tra tên chức vụ đã tồn tại chưa
        if (await _context.Positions.AnyAsync(p => p.Name == request.Name))
            return Conflict(new { message = $"Chức vụ '{request.Name}' đã tồn tại" });

        var position = new Position
        {
            Name = request.Name
        };

        _context.Positions.Add(position);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = position.PositionId }, new PositionResponse
        {
            PositionId = position.PositionId,
            Name = position.Name,
            EmployeeCount = 0
        });
    }

    /// <summary>Cập nhật tên chức vụ (chỉ Admin)</summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdatePositionRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var position = await _context.Positions.FindAsync(id);
        if (position == null)
            return NotFound(new { message = $"Không tìm thấy chức vụ ID {id}" });

        // Kiểm tra tên trùng với chức vụ khác
        if (await _context.Positions.AnyAsync(p => p.Name == request.Name && p.PositionId != id))
            return Conflict(new { message = $"Chức vụ '{request.Name}' đã tồn tại" });

        position.Name = request.Name;
        await _context.SaveChangesAsync();

        return Ok(new PositionResponse
        {
            PositionId = position.PositionId,
            Name = position.Name,
            EmployeeCount = _context.Employees.Count(e => e.PositionId == id)
        });
    }

    /// <summary>Xóa chức vụ (chỉ Admin). Không thể xóa nếu còn nhân viên.</summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var position = await _context.Positions
            .Include(p => p.Employees)
            .FirstOrDefaultAsync(p => p.PositionId == id);

        if (position == null)
            return NotFound(new { message = $"Không tìm thấy chức vụ ID {id}" });

        if (position.Employees.Any())
            return BadRequest(new { message = $"Không thể xóa chức vụ đang có {position.Employees.Count} nhân viên. Hãy chuyển nhân viên sang chức vụ khác trước." });

        _context.Positions.Remove(position);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}

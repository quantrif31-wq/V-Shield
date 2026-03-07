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
public class DepartmentsController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public DepartmentsController(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <summary>Lấy danh sách tất cả phòng ban (chỉ Admin)</summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var departments = await _context.Departments
            .OrderBy(d => d.DepartmentId)
            .Select(d => new DepartmentResponse
            {
                DepartmentId = d.DepartmentId,
                Name = d.Name,
                EmployeeCount = d.Employees.Count
            })
            .ToListAsync();

        return Ok(departments);
    }

    /// <summary>Lấy thông tin phòng ban theo ID (chỉ Admin)</summary>
    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var department = await _context.Departments
            .Include(d => d.Employees)
            .FirstOrDefaultAsync(d => d.DepartmentId == id);

        if (department == null)
            return NotFound(new { message = $"Không tìm thấy phòng ban ID {id}" });

        return Ok(new DepartmentResponse
        {
            DepartmentId = department.DepartmentId,
            Name = department.Name,
            EmployeeCount = department.Employees.Count
        });
    }

    /// <summary>Tạo phòng ban mới (chỉ Admin)</summary>
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateDepartmentRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        // Kiểm tra tên phòng ban đã tồn tại chưa
        if (await _context.Departments.AnyAsync(d => d.Name == request.Name))
            return Conflict(new { message = $"Phòng ban '{request.Name}' đã tồn tại" });

        var department = new Department
        {
            Name = request.Name
        };

        _context.Departments.Add(department);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = department.DepartmentId }, new DepartmentResponse
        {
            DepartmentId = department.DepartmentId,
            Name = department.Name,
            EmployeeCount = 0
        });
    }

    /// <summary>Cập nhật tên phòng ban (chỉ Admin)</summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateDepartmentRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var department = await _context.Departments.FindAsync(id);
        if (department == null)
            return NotFound(new { message = $"Không tìm thấy phòng ban ID {id}" });

        // Kiểm tra tên trùng với phòng ban khác
        if (await _context.Departments.AnyAsync(d => d.Name == request.Name && d.DepartmentId != id))
            return Conflict(new { message = $"Phòng ban '{request.Name}' đã tồn tại" });

        department.Name = request.Name;
        await _context.SaveChangesAsync();

        return Ok(new DepartmentResponse
        {
            DepartmentId = department.DepartmentId,
            Name = department.Name,
            EmployeeCount = _context.Employees.Count(e => e.DepartmentId == id)
        });
    }

    /// <summary>Xóa phòng ban (chỉ Admin). Không thể xóa nếu còn nhân viên.</summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var department = await _context.Departments
            .Include(d => d.Employees)
            .FirstOrDefaultAsync(d => d.DepartmentId == id);

        if (department == null)
            return NotFound(new { message = $"Không tìm thấy phòng ban ID {id}" });

        if (department.Employees.Any())
            return BadRequest(new { message = $"Không thể xóa phòng ban đang có {department.Employees.Count} nhân viên. Hãy chuyển nhân viên sang phòng ban khác trước." });

        _context.Departments.Remove(department);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}

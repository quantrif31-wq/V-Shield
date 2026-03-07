using API.Data;
using API.DTOs;
using API.Hubs;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.EntityFrameworkCore;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class EmployeesController : ControllerBase
{
    private readonly ApplicationDbContext _context;
    private readonly IHubContext<EmployeeStatsHub> _hubContext;

    public EmployeesController(ApplicationDbContext context, IHubContext<EmployeeStatsHub> hubContext)
    {
        _context = context;
        _hubContext = hubContext;
    }

    /// <summary>Lấy danh sách tất cả nhân viên (chỉ Admin)</summary>
    [HttpGet]
    public async Task<IActionResult> GetAll(
        [FromQuery] string? search,
        [FromQuery] int? departmentId,
        [FromQuery] int? positionId,
        [FromQuery] bool? status)
    {
        var query = _context.Employees
            .Include(e => e.Department)
            .Include(e => e.Position)
            .AsQueryable();

        // Lọc theo tên hoặc email
        if (!string.IsNullOrWhiteSpace(search))
            query = query.Where(e =>
                e.FullName.Contains(search) ||
                (e.Email != null && e.Email.Contains(search)) ||
                (e.Phone != null && e.Phone.Contains(search)));

        if (departmentId.HasValue)
            query = query.Where(e => e.DepartmentId == departmentId);

        if (positionId.HasValue)
            query = query.Where(e => e.PositionId == positionId);

        if (status.HasValue)
            query = query.Where(e => e.Status == status);

        var employees = await query
            .OrderBy(e => e.FullName)
            .Select(e => new EmployeeResponse
            {
                EmployeeId = e.EmployeeId,
                FullName = e.FullName,
                Phone = e.Phone,
                Email = e.Email,
                FaceImageUrl = e.FaceImageUrl,
                Status = e.Status,
                DepartmentId = e.DepartmentId,
                DepartmentName = e.Department != null ? e.Department.Name : null,
                PositionId = e.PositionId,
                PositionName = e.Position != null ? e.Position.Name : null
            })
            .ToListAsync();

        return Ok(employees);
    }

    /// <summary>Lấy thông tin 1 nhân viên theo ID (chỉ Admin)</summary>
    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var e = await _context.Employees
            .Include(x => x.Department)
            .Include(x => x.Position)
            .FirstOrDefaultAsync(x => x.EmployeeId == id);

        if (e == null)
            return NotFound(new { message = $"Không tìm thấy nhân viên ID {id}" });

        return Ok(new EmployeeResponse
        {
            EmployeeId = e.EmployeeId,
            FullName = e.FullName,
            Phone = e.Phone,
            Email = e.Email,
            FaceImageUrl = e.FaceImageUrl,
            Status = e.Status,
            DepartmentId = e.DepartmentId,
            DepartmentName = e.Department?.Name,
            PositionId = e.PositionId,
            PositionName = e.Position?.Name
        });
    }

    /// <summary>Tạo nhân viên mới (chỉ Admin)</summary>
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateEmployeeRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        // Kiểm tra DepartmentId hợp lệ
        if (request.DepartmentId.HasValue &&
            !await _context.Departments.AnyAsync(d => d.DepartmentId == request.DepartmentId))
            return BadRequest(new { message = $"DepartmentId {request.DepartmentId} không tồn tại" });

        // Kiểm tra PositionId hợp lệ
        if (request.PositionId.HasValue &&
            !await _context.Positions.AnyAsync(p => p.PositionId == request.PositionId))
            return BadRequest(new { message = $"PositionId {request.PositionId} không tồn tại" });

        var employee = new Employee
        {
            FullName = request.FullName,
            DepartmentId = request.DepartmentId,
            PositionId = request.PositionId,
            Phone = request.Phone,
            Email = request.Email,
            FaceImageUrl = request.FaceImageUrl,
            Status = request.Status
        };

        _context.Employees.Add(employee);
        await _context.SaveChangesAsync();

        // Load navigation properties sau khi save
        await _context.Entry(employee).Reference(e => e.Department).LoadAsync();
        await _context.Entry(employee).Reference(e => e.Position).LoadAsync();

        // Broadcast real-time update tới clients đang theo dõi
        int total = await _context.Employees.CountAsync();
        int active = await _context.Employees.CountAsync(e => e.Status == true);
        await _hubContext.Clients.Group("stats").SendAsync("ReceiveStatsUpdate", new EmployeeCountChangedEvent
        {
            TotalEmployees = total,
            ActiveEmployees = active,
            ChangeType = "created",
            ChangedAt = DateTime.Now
        });

        return CreatedAtAction(nameof(GetById), new { id = employee.EmployeeId }, new EmployeeResponse
        {
            EmployeeId = employee.EmployeeId,
            FullName = employee.FullName,
            Phone = employee.Phone,
            Email = employee.Email,
            FaceImageUrl = employee.FaceImageUrl,
            Status = employee.Status,
            DepartmentId = employee.DepartmentId,
            DepartmentName = employee.Department?.Name,
            PositionId = employee.PositionId,
            PositionName = employee.Position?.Name
        });
    }

    /// <summary>Cập nhật nhân viên (chỉ Admin)</summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateEmployeeRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var employee = await _context.Employees
            .Include(e => e.Department)
            .Include(e => e.Position)
            .FirstOrDefaultAsync(e => e.EmployeeId == id);

        if (employee == null)
            return NotFound(new { message = $"Không tìm thấy nhân viên ID {id}" });

        if (request.FullName != null)
            employee.FullName = request.FullName;

        if (request.DepartmentId.HasValue)
        {
            if (!await _context.Departments.AnyAsync(d => d.DepartmentId == request.DepartmentId))
                return BadRequest(new { message = $"DepartmentId {request.DepartmentId} không tồn tại" });
            employee.DepartmentId = request.DepartmentId;
        }

        if (request.PositionId.HasValue)
        {
            if (!await _context.Positions.AnyAsync(p => p.PositionId == request.PositionId))
                return BadRequest(new { message = $"PositionId {request.PositionId} không tồn tại" });
            employee.PositionId = request.PositionId;
        }

        if (request.Phone != null) employee.Phone = request.Phone;
        if (request.Email != null) employee.Email = request.Email;
        if (request.FaceImageUrl != null) employee.FaceImageUrl = request.FaceImageUrl;
        if (request.Status.HasValue) employee.Status = request.Status;

        await _context.SaveChangesAsync();

        // Reload navigation properties
        await _context.Entry(employee).Reference(e => e.Department).LoadAsync();
        await _context.Entry(employee).Reference(e => e.Position).LoadAsync();

        return Ok(new EmployeeResponse
        {
            EmployeeId = employee.EmployeeId,
            FullName = employee.FullName,
            Phone = employee.Phone,
            Email = employee.Email,
            FaceImageUrl = employee.FaceImageUrl,
            Status = employee.Status,
            DepartmentId = employee.DepartmentId,
            DepartmentName = employee.Department?.Name,
            PositionId = employee.PositionId,
            PositionName = employee.Position?.Name
        });
    }

    /// <summary>Xóa nhân viên (chỉ Admin)</summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var employee = await _context.Employees.FindAsync(id);
        if (employee == null)
            return NotFound(new { message = $"Không tìm thấy nhân viên ID {id}" });

        _context.Employees.Remove(employee);
        await _context.SaveChangesAsync();

        // Broadcast real-time update tới clients đang theo dõi
        int total = await _context.Employees.CountAsync();
        int active = await _context.Employees.CountAsync(e => e.Status == true);
        await _hubContext.Clients.Group("stats").SendAsync("ReceiveStatsUpdate", new EmployeeCountChangedEvent
        {
            TotalEmployees = total,
            ActiveEmployees = active,
            ChangeType = "deleted",
            ChangedAt = DateTime.Now
        });

        return NoContent();
    }

    /// <summary>Upload ảnh khuôn mặt nhân viên từ file máy tính (chỉ Admin)</summary>
    [HttpPost("{id}/face")]
    [Consumes("multipart/form-data")]
    public async Task<IActionResult> UploadFace(int id, IFormFile file)
    {
        var employee = await _context.Employees.FindAsync(id);
        if (employee == null)
            return NotFound(new { message = $"Không tìm thấy nhân viên ID {id}" });

        if (file == null || file.Length == 0)
            return BadRequest(new { message = "Vui lòng chọn file ảnh" });

        // Kiểm tra định dạng file
        var allowedTypes = new[] { "image/jpeg", "image/png", "image/webp", "image/jpg" };
        if (!allowedTypes.Contains(file.ContentType.ToLower()))
            return BadRequest(new { message = "Chỉ chấp nhận file ảnh (JPG, PNG, WebP)" });

        // Giới hạn dung lượng 5MB
        if (file.Length > 5 * 1024 * 1024)
            return BadRequest(new { message = "Kích thước ảnh không được vượt quá 5MB" });

        // Tạo thư mục lưu ảnh nếu chưa có
        var uploadFolder = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "uploads", "faces");
        Directory.CreateDirectory(uploadFolder);

        // Xóa ảnh cũ nếu có
        if (!string.IsNullOrEmpty(employee.FaceImageUrl))
        {
            var oldFileName = Path.GetFileName(employee.FaceImageUrl);
            var oldFilePath = Path.Combine(uploadFolder, oldFileName);
            if (System.IO.File.Exists(oldFilePath))
                System.IO.File.Delete(oldFilePath);
        }

        // Tạo tên file duy nhất
        var ext = Path.GetExtension(file.FileName).ToLower();
        var newFileName = $"emp_{id}_{Guid.NewGuid():N}{ext}";
        var newFilePath = Path.Combine(uploadFolder, newFileName);

        // Lưu file
        using (var stream = new FileStream(newFilePath, FileMode.Create))
            await file.CopyToAsync(stream);

        // Cập nhật URL vào DB (dạng path tương đối để serve qua static files)
        employee.FaceImageUrl = $"/uploads/faces/{newFileName}";
        await _context.SaveChangesAsync();

        return Ok(new
        {
            message = "Upload ảnh thành công",
            employeeId = id,
            faceImageUrl = employee.FaceImageUrl
        });
    }
}

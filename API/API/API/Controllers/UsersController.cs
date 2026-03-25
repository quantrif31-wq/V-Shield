using API.Data;
using API.DTOs;
using API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Security.Claims;

namespace API.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class UsersController : ControllerBase
{
    private readonly ApplicationDbContext _context;

    public UsersController(ApplicationDbContext context)
    {
        _context = context;
    }

    /// <summary>Lấy danh sách tất cả tài khoản (chỉ Admin)</summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var users = await _context.AppUsers
            .OrderBy(u => u.UserId)
            .Select(u => new UserResponse
            {
                UserId = u.UserId,
                Username = u.Username,
                FullName = u.FullName,
                Role = u.Role,
                IsActive = u.IsActive,
                CreatedAt = u.CreatedAt,
                EmployeeId = u.EmployeeId
            })
            .ToListAsync();

        return Ok(users);
    }

    /// <summary>Lấy thông tin tài khoản theo ID (chỉ Admin)</summary>
    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(int id)
    {
        var user = await _context.AppUsers.FindAsync(id);
        if (user == null)
            return NotFound(new { message = $"Không tìm thấy tài khoản ID {id}" });

        return Ok(new UserResponse
        {
            UserId = user.UserId,
            Username = user.Username,
            FullName = user.FullName,
            Role = user.Role,
            IsActive = user.IsActive,
            CreatedAt = user.CreatedAt,
            EmployeeId = user.EmployeeId
        });
    }

    /// <summary>Tạo tài khoản mới (chỉ Admin)</summary>
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateUserRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        // Kiểm tra username đã tồn tại chưa
        if (await _context.AppUsers.AnyAsync(u => u.Username == request.Username))
            return Conflict(new { message = $"Tên đăng nhập '{request.Username}' đã tồn tại" });

        if (request.EmployeeId.HasValue && request.EmployeeId.Value > 0)
        {
            if (!await _context.Employees.AnyAsync(e => e.EmployeeId == request.EmployeeId))
                return BadRequest(new { message = $"EmployeeID {request.EmployeeId} không tồn tại" });
        }

        var user = new AppUser
        {
            Username = request.Username,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password),
            FullName = request.FullName,
            Role = request.Role,
            IsActive = true,
            CreatedAt = DateTime.UtcNow,
            EmployeeId = (request.EmployeeId.HasValue && request.EmployeeId.Value > 0) ? request.EmployeeId : null
        };

        _context.AppUsers.Add(user);
        await _context.SaveChangesAsync();

        return CreatedAtAction(nameof(GetById), new { id = user.UserId }, new UserResponse
        {
            UserId = user.UserId,
            Username = user.Username,
            FullName = user.FullName,
            Role = user.Role,
            IsActive = user.IsActive,
            CreatedAt = user.CreatedAt,
            EmployeeId = user.EmployeeId
        });
    }

    /// <summary>Cập nhật tài khoản (chỉ Admin)</summary>
    [HttpPut("{id}")]
    public async Task<IActionResult> Update(int id, [FromBody] UpdateUserRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        var user = await _context.AppUsers.FindAsync(id);
        if (user == null)
            return NotFound(new { message = $"Không tìm thấy tài khoản ID {id}" });

        if (request.FullName != null)
            user.FullName = request.FullName;

        if (request.Role != null)
            user.Role = request.Role;

        if (request.IsActive.HasValue)
            user.IsActive = request.IsActive.Value;

        if (!string.IsNullOrWhiteSpace(request.Password))
            user.PasswordHash = BCrypt.Net.BCrypt.HashPassword(request.Password);

        if (request.EmployeeId.HasValue)
        {
            if (request.EmployeeId.Value > 0)
            {
                if (!await _context.Employees.AnyAsync(e => e.EmployeeId == request.EmployeeId))
                    return BadRequest(new { message = $"EmployeeID {request.EmployeeId} không tồn tại" });
                user.EmployeeId = request.EmployeeId;
            }
            else
            {
                user.EmployeeId = null;
            }
        }

        await _context.SaveChangesAsync();

        return Ok(new UserResponse
        {
            UserId = user.UserId,
            Username = user.Username,
            FullName = user.FullName,
            Role = user.Role,
            IsActive = user.IsActive,
            CreatedAt = user.CreatedAt,
            EmployeeId = user.EmployeeId
        });
    }

    /// <summary>Xóa tài khoản (chỉ Admin). Không thể xóa chính mình.</summary>
    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(int id)
    {
        var user = await _context.AppUsers.FindAsync(id);
        if (user == null)
            return NotFound(new { message = $"Không tìm thấy tài khoản ID {id}" });

        // Lấy ID người dùng hiện tại để tránh tự xóa mình
        var currentUserIdClaim = User.FindFirstValue(System.IdentityModel.Tokens.Jwt.JwtRegisteredClaimNames.Sub);
        if (currentUserIdClaim != null && int.TryParse(currentUserIdClaim, out var currentUserId) && currentUserId == id)
            return BadRequest(new { message = "Không thể xóa tài khoản đang đăng nhập" });

        _context.AppUsers.Remove(user);
        await _context.SaveChangesAsync();

        return NoContent();
    }
}

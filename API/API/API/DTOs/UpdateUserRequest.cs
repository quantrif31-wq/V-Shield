using System.ComponentModel.DataAnnotations;

namespace API.DTOs;

public class UpdateUserRequest
{
    [MaxLength(100)]
    public string? FullName { get; set; }

    /// <summary>Admin | Staff | BaoVe</summary>
    [RegularExpression("^(Admin|Staff|BaoVe)$", ErrorMessage = "Role phải là Admin, Staff hoặc BaoVe")]
    public string? Role { get; set; }

    public bool? IsActive { get; set; }

    /// <summary>Để trống nếu không muốn đổi mật khẩu</summary>
    [MinLength(6)]
    public string? Password { get; set; }

    public int? EmployeeId { get; set; }
}

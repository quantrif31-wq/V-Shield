using System.ComponentModel.DataAnnotations;

namespace API.DTOs;

public class CreateUserRequest
{
    [Required]
    [MaxLength(50)]
    public string Username { get; set; } = null!;

    [Required]
    [MinLength(6)]
    public string Password { get; set; } = null!;

    [MaxLength(100)]
    public string? FullName { get; set; }

    /// <summary>Admin | Staff | BaoVe</summary>
    [Required]
    [RegularExpression("^(Admin|Staff|BaoVe)$", ErrorMessage = "Role phải là Admin, Staff hoặc BaoVe")]
    public string Role { get; set; } = "Staff";

    public int? EmployeeId { get; set; }
}

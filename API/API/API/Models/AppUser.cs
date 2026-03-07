using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace API.Models;

[Table("AppUsers")]
public class AppUser
{
    [Key]
    public int UserId { get; set; }

    [Required]
    [MaxLength(50)]
    public string Username { get; set; } = null!;

    [Required]
    [MaxLength(255)]
    public string PasswordHash { get; set; } = null!;

    [MaxLength(100)]
    public string? FullName { get; set; }

    /// <summary>Admin | Staff | BaoVe</summary>
    [Required]
    [MaxLength(20)]
    public string Role { get; set; } = "Staff";

    public bool IsActive { get; set; } = true;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

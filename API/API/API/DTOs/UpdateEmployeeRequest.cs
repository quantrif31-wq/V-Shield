using System.ComponentModel.DataAnnotations;

namespace API.DTOs;

public class UpdateEmployeeRequest
{
    [MaxLength(150)]
    public string? FullName { get; set; }

    public int? DepartmentId { get; set; }

    public int? PositionId { get; set; }

    [MaxLength(20)]
    public string? Phone { get; set; }

    [MaxLength(100)]
    [EmailAddress]
    public string? Email { get; set; }

    [MaxLength(300)]
    public string? FaceImageUrl { get; set; }

    public bool? Status { get; set; }
}

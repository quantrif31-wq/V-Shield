namespace API.DTOs;

public class EmployeeResponse
{
    public int EmployeeId { get; set; }
    public string FullName { get; set; } = null!;
    public string? Phone { get; set; }
    public string? Email { get; set; }
    public string? FaceImageUrl { get; set; }
    public bool? Status { get; set; }

    // Department info
    public int? DepartmentId { get; set; }
    public string? DepartmentName { get; set; }

    // Position info
    public int? PositionId { get; set; }
    public string? PositionName { get; set; }
}

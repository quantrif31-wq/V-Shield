using System.ComponentModel.DataAnnotations;

namespace API.DTOs;

public class CreatePositionRequest
{
    [Required(ErrorMessage = "Tên chức vụ không được để trống")]
    [StringLength(100, ErrorMessage = "Tên chức vụ tối đa 100 ký tự")]
    public string Name { get; set; } = null!;
}

public class UpdatePositionRequest
{
    [Required(ErrorMessage = "Tên chức vụ không được để trống")]
    [StringLength(100, ErrorMessage = "Tên chức vụ tối đa 100 ký tự")]
    public string Name { get; set; } = null!;
}

public class PositionResponse
{
    public int PositionId { get; set; }
    public string Name { get; set; } = null!;
    public int EmployeeCount { get; set; }
}

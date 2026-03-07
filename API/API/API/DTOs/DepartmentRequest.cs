using System.ComponentModel.DataAnnotations;

namespace API.DTOs;

public class CreateDepartmentRequest
{
    [Required(ErrorMessage = "Tên phòng ban không được để trống")]
    [StringLength(100, ErrorMessage = "Tên phòng ban tối đa 100 ký tự")]
    public string Name { get; set; } = null!;
}

public class UpdateDepartmentRequest
{
    [Required(ErrorMessage = "Tên phòng ban không được để trống")]
    [StringLength(100, ErrorMessage = "Tên phòng ban tối đa 100 ký tự")]
    public string Name { get; set; } = null!;
}

public class DepartmentResponse
{
    public int DepartmentId { get; set; }
    public string Name { get; set; } = null!;
    public int EmployeeCount { get; set; }
}

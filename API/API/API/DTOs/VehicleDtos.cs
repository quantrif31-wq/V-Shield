namespace API.DTOs;

using System.ComponentModel.DataAnnotations;

// DTO trả về thông tin phương tiện
public class VehicleDto
{
    public int VehicleId { get; set; }
    public string LicensePlate { get; set; } = null!;
    public int? VehicleTypeId { get; set; }
    public string? VehicleTypeName { get; set; }
    public int? EmployeeId { get; set; }
    public string? EmployeeFullName { get; set; }
    public string? Description { get; set; }
}

// DTO tạo mới phương tiện
public class CreateVehicleDto
{
    [Required]
    [StringLength(20, ErrorMessage = "Biển số không được vượt quá 20 ký tự.")]
    public string LicensePlate { get; set; } = null!;

    public int? VehicleTypeId { get; set; }

    [Required(ErrorMessage = "Mã nhân viên là bắt buộc.")]
    public int EmployeeId { get; set; }

    [StringLength(200, ErrorMessage = "Mô tả không được vượt quá 200 ký tự.")]
    public string? Description { get; set; }
}

// DTO cập nhật phương tiện
public class UpdateVehicleDto
{
    [StringLength(20, ErrorMessage = "Biển số không được vượt quá 20 ký tự.")]
    public string? LicensePlate { get; set; }

    public int? VehicleTypeId { get; set; }

    public int? EmployeeId { get; set; }

    [StringLength(200, ErrorMessage = "Mô tả không được vượt quá 200 ký tự.")]
    public string? Description { get; set; }
}

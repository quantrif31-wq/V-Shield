using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace API.DTOs.PreRegistration;

// ════════════════════════════════════════════════════════
// REQUEST DTOs
// ════════════════════════════════════════════════════════

/// <summary>Nhân viên tạo link đăng ký</summary>
public class CreateLinkRequestDto
{
    [Required]
    public int HostEmployeeId { get; set; }

    [Range(1, 168)] // tối đa 7 ngày
    public int ExpiryHours { get; set; } = 24;
}

/// <summary>Guest submit form đăng ký</summary>
public class SubmitRegistrationDto
{
    // ── Thông tin người đăng ký chính (chỉ là đầu mối liên hệ) ──
    [Required, StringLength(150)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? Phone { get; set; }

    // ── Thông tin xe ──────────────────────────────────────
    [Required, StringLength(20)]
    public string ExpectedLicensePlate { get; set; } = null!;

    [Required]
    public DateTime ExpectedTimeIn { get; set; }

    [Required]
    public DateTime ExpectedTimeOut { get; set; }

    // ── Danh sách người ngồi trên xe ─────────────────────
    [Range(1, 50)]
    public int NumberOfVisitors { get; set; } = 1;

    public List<VisitorInfoDto> Visitors { get; set; } = new();
}

/// <summary>Thông tin từng người trong đoàn</summary>
public class VisitorInfoDto
{
    [Required, StringLength(100)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? IdCardNumber { get; set; }

    /// <summary>Ảnh mặt đăng ký trước — dùng để so sánh khi quét</summary>
    public string? ExpectedFaceImage { get; set; }
}

public class UpdateStatusDto
{
    [Required]
    [RegularExpression("Approved|Rejected|Pending",
        ErrorMessage = "Status phải là Approved, Rejected hoặc Pending")]
    public string Status { get; set; } = null!;
}

// ════════════════════════════════════════════════════════
// RESPONSE DTOs
// ════════════════════════════════════════════════════════

public class CreateLinkResponseDto
{
    public string Token { get; set; } = null!;
    public string RegistrationUrl { get; set; } = null!;
    public DateTime ExpiredAt { get; set; }
}

public class ValidateTokenResponseDto
{
    public string HostEmployeeName { get; set; } = null!;
    public string? HostEmployeePhone { get; set; }
    public string? HostEmployeeEmail { get; set; }
    public string? HostDepartmentName { get; set; }
    public string? HostPositionName { get; set; }
    public string? HostFaceImageUrl { get; set; }
    public List<string>? HostLicensePlates { get; set; }
    public DateTime ExpiredAt { get; set; }
}

public class RegistrationListItemDto
{
    public int RegistrationId { get; set; }
    public int GuestId { get; set; }
    public string GuestFullName { get; set; } = null!;
    public string? GuestPhone { get; set; }
    public string? ExpectedLicensePlate { get; set; }
    public DateTime ExpectedTimeIn { get; set; }
    public DateTime ExpectedTimeOut { get; set; }
    public int NumberOfVisitors { get; set; }
    public string? Status { get; set; }
    public string HostEmployeeName { get; set; } = null!;
    public DateTime CreatedAt { get; set; }
}

/// <summary>Chi tiết đơn đăng ký — bao gồm danh sách visitor và access logs</summary>
public class RegistrationDetailDto : RegistrationListItemDto
{
    public List<VisitorInfoDto> Visitors { get; set; } = new();
    public List<AccessLogDto> AccessLogs { get; set; } = new();
}

public class AccessLogDto
{
    public int LogId { get; set; }
    public DateTime? Timestamp { get; set; }
    public string Direction { get; set; } = null!; // "IN" / "OUT"
    public string? CapturedLicensePlate { get; set; }
    public string? ResultStatus { get; set; }
    public string? Note { get; set; }
}
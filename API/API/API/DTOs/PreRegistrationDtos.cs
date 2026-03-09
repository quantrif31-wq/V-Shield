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

    /// <summary>Link hết hạn sau N giờ (default 24h)</summary>
    [Range(1, 168)] // tối đa 7 ngày
    public int ExpiryHours { get; set; } = 24;
}

/// <summary>Guest submit form đăng ký</summary>
public class SubmitRegistrationDto
{
    // ── Thông tin người đăng ký chính ────────────────────
    [Required, StringLength(150)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? Phone { get; set; }

    /// <summary>
    /// Ảnh mặt dạng base64 — lưu vào GuestProfile.FaceImageUrl
    /// Format: "data:image/jpeg;base64,/9j/4AAQ..."
    /// </summary>
    public string? FaceImageBase64 { get; set; }

    // ── Thông tin chuyến thăm ─────────────────────────────
    [Required, StringLength(20)]
    public string ExpectedLicensePlate { get; set; } = null!;

    /// <summary>
    /// Ảnh biển số dạng base64 — lưu vào PreRegistration
    /// Format: "data:image/jpeg;base64,/9j/4AAQ..."
    /// </summary>
    public string? LicensePlateImageBase64 { get; set; }

    [Required]
    public DateTime ExpectedTimeIn { get; set; }

    [Required]
    public DateTime ExpectedTimeOut { get; set; }

    // ── Đoàn khách ───────────────────────────────────────
    [Range(1, 50)]
    public int NumberOfVisitors { get; set; } = 1;

    public List<VisitorInfoDto> Visitors { get; set; } = new();
}

public class VisitorInfoDto
{
    [Required, StringLength(100)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? IdCardNumber { get; set; }
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

public class RegistrationDetailDto : RegistrationListItemDto
{
    /// <summary>Ảnh mặt — lấy từ GuestProfile.FaceImageUrl</summary>
    public string? FaceImageUrl { get; set; }

    /// <summary>Ảnh biển số — lấy từ PreRegistration</summary>
    public string? LicensePlateImageBase64 { get; set; }

    public List<VisitorInfoDto> Visitors { get; set; } = new();
    public List<AccessLogDto> AccessLogs { get; set; } = new();
}

public class AccessLogDto
{
    public int LogId { get; set; }
    public DateTime? Timestamp { get; set; }
    public string Direction { get; set; } = null!; // "IN" hoặc "OUT"
    public string? CapturedLicensePlate { get; set; }
    public string? ResultStatus { get; set; }
    public string? Note { get; set; }
}
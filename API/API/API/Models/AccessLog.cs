using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Access_Log")]
public partial class AccessLog
{
    [Key]
    public int LogId { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime? Timestamp { get; set; }

    [StringLength(10)]
    [Unicode(false)]
    public string Direction { get; set; } = null!;

    public int? GateId { get; set; }

    public int? CameraId { get; set; }

    [StringLength(20)]
    public string? CapturedLicensePlate { get; set; }

    [Column("CapturedFaceImageURL")]
    [StringLength(300)]
    public string? CapturedFaceImageUrl { get; set; }

    public int? EmployeeId { get; set; }

    public int? RegistrationId { get; set; }

    [StringLength(20)]
    [Unicode(false)]
    public string ResultStatus { get; set; } = null!;

    public bool? IsBypass { get; set; }

    public int? ExceptionReasonId { get; set; }

    [StringLength(500)]
    public string? Note { get; set; }

    public int? EntryLogId { get; set; }

    [ForeignKey("CameraId")]
    [InverseProperty("AccessLogs")]
    public virtual Camera? Camera { get; set; }

    [ForeignKey("EmployeeId")]
    [InverseProperty("AccessLogs")]
    public virtual Employee? Employee { get; set; }

    [ForeignKey("EntryLogId")]
    [InverseProperty("InverseEntryLog")]
    public virtual AccessLog? EntryLog { get; set; }

    [ForeignKey("ExceptionReasonId")]
    [InverseProperty("AccessLogs")]
    public virtual ExceptionReason? ExceptionReason { get; set; }

    [ForeignKey("GateId")]
    [InverseProperty("AccessLogs")]
    public virtual Gate? Gate { get; set; }

    [InverseProperty("EntryLog")]
    public virtual ICollection<AccessLog> InverseEntryLog { get; set; } = new List<AccessLog>();

    [ForeignKey("RegistrationId")]
    [InverseProperty("AccessLogs")]
    public virtual PreRegistration? Registration { get; set; }
}

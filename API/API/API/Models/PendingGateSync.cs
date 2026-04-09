using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Pending_Gate_Sync")]
public class PendingGateSync
{
    [Key]
    public int PendingGateSyncId { get; set; }

    public int AccessLogId { get; set; }

    public int EmployeeId { get; set; }

    [StringLength(20)]
    public string LicensePlate { get; set; } = string.Empty;

    public int? VehicleTypeId { get; set; }

    public int? GateId { get; set; }

    public int? CameraId { get; set; }

    [StringLength(500)]
    public string? Description { get; set; }

    [StringLength(20)]
    [Unicode(false)]
    public string Status { get; set; } = "PENDING";

    [Column(TypeName = "datetime")]
    public DateTime CreatedAt { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime SyncDueAt { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime? LastAttemptAt { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime? SyncedAt { get; set; }

    public int RetryCount { get; set; }

    [StringLength(500)]
    public string? LastError { get; set; }

    [StringLength(500)]
    public string? RemoteMessage { get; set; }
}

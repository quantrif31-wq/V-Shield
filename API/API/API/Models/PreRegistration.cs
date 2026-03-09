using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Pre_Registration")]
public partial class PreRegistration
{
    [Key]
    public int RegistrationId { get; set; }

    public int? GuestId { get; set; }

    public int? HostEmployeeId { get; set; }

    [StringLength(20)]
    public string? ExpectedLicensePlate { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime ExpectedTimeIn { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime ExpectedTimeOut { get; set; }

    [StringLength(50)]
    [Unicode(false)]
    public string? Status { get; set; }

    [InverseProperty("Registration")]
    public virtual ICollection<AccessLog> AccessLogs { get; set; } = new List<AccessLog>();

    [ForeignKey("GuestId")]
    [InverseProperty("PreRegistrations")]
    public virtual GuestProfile? Guest { get; set; }

    [ForeignKey("HostEmployeeId")]
    [InverseProperty("PreRegistrations")]
    public virtual Employee? HostEmployee { get; set; }

    public int NumberOfVisitors { get; set; } = 1;

    [Column(TypeName = "datetime")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    // ── Navigation mới ───────────────────────────────────────

    [InverseProperty("Registration")]
    public virtual ICollection<VisitorDetail> VisitorDetails { get; set; } = new List<VisitorDetail>();
}


using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Gate")]
public partial class Gate
{
    [Key]
    public int GateId { get; set; }

    [StringLength(100)]
    public string GateName { get; set; } = null!;

    [StringLength(200)]
    public string? Location { get; set; }

    [InverseProperty("Gate")]
    public virtual ICollection<AccessLog> AccessLogs { get; set; } = new List<AccessLog>();

    [InverseProperty("Gate")]
    public virtual ICollection<Camera> Cameras { get; set; } = new List<Camera>();
}

using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Camera")]
public partial class Camera
{
    [Key]
    public int CameraId { get; set; }

    [StringLength(100)]
    public string CameraName { get; set; } = null!;

    public int? GateId { get; set; }

    [StringLength(50)]
    [Unicode(false)]
    public string? CameraType { get; set; }

    [InverseProperty("Camera")]
    public virtual ICollection<AccessLog> AccessLogs { get; set; } = new List<AccessLog>();

    [ForeignKey("GateId")]
    [InverseProperty("Cameras")]
    public virtual Gate? Gate { get; set; }
}

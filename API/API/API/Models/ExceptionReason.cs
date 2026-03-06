using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Exception_Reason")]
[Index("ReasonCode", Name = "UQ__Exceptio__A6278DA348D14177", IsUnique = true)]
public partial class ExceptionReason
{
    [Key]
    public int ReasonId { get; set; }

    [StringLength(50)]
    [Unicode(false)]
    public string ReasonCode { get; set; } = null!;

    [StringLength(200)]
    public string Description { get; set; } = null!;

    [InverseProperty("ExceptionReason")]
    public virtual ICollection<AccessLog> AccessLogs { get; set; } = new List<AccessLog>();
}

using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Registration_Links")]
public class RegistrationLink
{
    [Key]
    public int LinkId { get; set; }

    [Required]
    [StringLength(32)]
    [Unicode(false)]
    public string Token { get; set; } = null!;

    public int HostEmployeeId { get; set; }

    [Column(TypeName = "datetime")]
    public DateTime ExpiredAt { get; set; }

    public bool IsUsed { get; set; } = false;

    [Column(TypeName = "datetime")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    [ForeignKey("HostEmployeeId")]
    public virtual Employee HostEmployee { get; set; } = null!;
}

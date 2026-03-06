using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("GuestProfile")]
public partial class GuestProfile
{
    [Key]
    public int GuestId { get; set; }

    [StringLength(150)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? Phone { get; set; }

    [StringLength(20)]
    public string? DefaultLicensePlate { get; set; }

    [Column("FaceImageURL")]
    [StringLength(300)]
    public string? FaceImageUrl { get; set; }

    [InverseProperty("Guest")]
    public virtual ICollection<PreRegistration> PreRegistrations { get; set; } = new List<PreRegistration>();
}

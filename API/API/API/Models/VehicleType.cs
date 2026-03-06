using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("VehicleType")]
public partial class VehicleType
{
    [Key]
    public int VehicleTypeId { get; set; }

    [StringLength(50)]
    public string TypeName { get; set; } = null!;

    [InverseProperty("VehicleType")]
    public virtual ICollection<Vehicle> Vehicles { get; set; } = new List<Vehicle>();
}

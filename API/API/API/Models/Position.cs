using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Position")]
public partial class Position
{
    [Key]
    public int PositionId { get; set; }

    [StringLength(100)]
    public string Name { get; set; } = null!;

    [InverseProperty("Position")]
    public virtual ICollection<Employee> Employees { get; set; } = new List<Employee>();
}

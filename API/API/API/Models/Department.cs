using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace API.Models;

[Table("Department")]
public partial class Department
{
    [Key]
    public int DepartmentId { get; set; }

    [StringLength(100)]
    public string Name { get; set; } = null!;

    [InverseProperty("Department")]
    public virtual ICollection<Employee> Employees { get; set; } = new List<Employee>();
}

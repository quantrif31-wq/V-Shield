using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace API.Models;

[Table("Visitor_Details")]
public class VisitorDetail
{
    [Key]
    public int VisitorDetailId { get; set; }

    public int RegistrationId { get; set; }

    [Required]
    [StringLength(100)]
    public string FullName { get; set; } = null!;

    [StringLength(20)]
    public string? IdCardNumber { get; set; }
    public string? ExpectedFaceImage { get; set; }

    [ForeignKey("RegistrationId")]
    [InverseProperty("VisitorDetails")]
    public virtual PreRegistration Registration { get; set; } = null!;
}

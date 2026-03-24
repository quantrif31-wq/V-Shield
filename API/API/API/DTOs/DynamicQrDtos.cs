using System.ComponentModel.DataAnnotations;

namespace API.Models.DTOs
{
    public class GenerateDynamicQrRequest
    {
        [Required]
        public int EmployeeId { get; set; }
    }

    public class VerifyDynamicQrRequest
    {
        [Required]
        public string QrPayload { get; set; } = string.Empty;

        public string? ScannerDevice { get; set; }
    }
}
using System;

namespace API.Models
{
    public class DynamicQrScanLog
    {
        public long Id { get; set; }

        public int EmployeeId { get; set; }

        public string QrPayload { get; set; } = string.Empty;

        public bool IsValid { get; set; }

        public string Message { get; set; } = string.Empty;

        public string? ScannerDevice { get; set; }

        public DateTime ScannedAt { get; set; } = DateTime.UtcNow;
    }
}